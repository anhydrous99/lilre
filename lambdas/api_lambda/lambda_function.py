from boto3.dynamodb.conditions import Key
from urllib3.exceptions import MaxRetryError, LocationParseError
from urllib.parse import urlparse
import urllib3
import logging
import decimal
import hashlib
import random
import string
import boto3
import json
import time
import abc

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
links_table = dynamodb.Table('Links')

allow_origin = 'https://site.lilre.link'
#allow_origin = '*'

# ----- Utility Functions and Classes -----

class DecimalDecoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return json.JSONEncoder.default(self, o)


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_website_live(url):
    http = urllib3.PoolManager()
    try:
        response = http.request('GET', url)
        return response.status == 200
    except (MaxRetryError, LocationParseError):
        return False


def good_to_create(url):
    return is_valid_url(url) and is_website_live(url)


def hash_dictionary(input_dict: dict):
    # Ensure that the dictionary only contains string keys
    for key in list(input_dict.keys()):
        if input_dict[key] is None:
            del input_dict[key]

    # Convert the dictionary to a JSON string
    json_str = json.dumps(input_dict, sort_keys=True)

    # Create a hashlib object and calculate the hash
    sha256 = hashlib.sha1()
    sha256.update(json_str.encode('utf-8'))
    hash_value = sha256.hexdigest()

    return hash_value


def generate_response(status_code, headers=None, body=None):
    response = {
        'statusCode': status_code
    }
    
    if headers is None:
        response['headers'] = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": allow_origin
        }
    else:
        response['headers'] = headers
        if 'Access-Control-Allow-Origin' not in response['headers']:
            response['headers']['Access-Control-Allow-Origin'] = allow_origin
    
    if body is not None:
        if not isinstance(body, str):
            body = json.dumps(body, cls=DecimalDecoder)
        response['body'] = body
    
    return response


# ---- API Functions

def get_userlinks(event):
    identity_hash = hash_dictionary(event['requestContext']['identity'])
    results = links_table.query(
        IndexName='identity-index',
        Select='ALL_ATTRIBUTES',
        KeyConditionExpression=Key('identity_hash').eq(identity_hash)
    )
    items = []
    if 'Items' in results:
        items.extend(results['Items'])
    return generate_response(200, body={'links': items})


def get_redirect_to_site(event):
    return generate_response(301, {'Location': 'https://site.lilre.link'})


def get_link(event, redirect):
    id = event['pathParameters']['id']
    returned = links_table.get_item(Key={'id': id})

    if 'Item' not in returned:
        return generate_response(404, body={'details': "Link not found."})
    
    if redirect:
        return generate_response(301, {'Location': returned['Item']['link']})
    else:
        return generate_response(200, body={'link': returned['Item']['link']})


def create_link(event):
    link = json.loads(event['body'])['link']

    if not good_to_create(link):
        return generate_response(412, body={'details': 'Link isn\'t valid or isn\'t live.'})
    
    id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    identity_hash = hash_dictionary(event['requestContext']['identity'])
    created_at = int(time.time())
    
    links_table.put_item(Item={'id': id, 'link': link, 'identity_hash': identity_hash, 'created_at': created_at})
    return generate_response(200, body={'path': id})


def delete_link(event):
    id = event['pathParameters']['id']
    response = links_table.delete_item(Key={'id': id})
    logger.info(response)

    return generate_response(200, body={'details': 'Done.'})


# ----- 


endpoints = {
    ('/userlinks', 'GET'): get_userlinks,
    ('/', 'GET'): get_redirect_to_site,
    ('/link/{id}', 'GET'): lambda event: get_link(event, False),
    ('/{id}', 'GET'): lambda event: get_link(event, True),
    ('/link', 'POST'): create_link,
    ('/link/{id}', 'DELETE'): delete_link
}


def lambda_handler(event, context):
    logger.info(json.dumps(event))

    method_resource = (event['resource'], event['httpMethod'])
    if method_resource not in endpoints:
        return generate_response(500, body={'details': 'Reached end.'})
    
    return endpoints[method_resource](event)
