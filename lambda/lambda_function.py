import random
import hashlib
import string
import boto3
import json
import time

import urllib3
from urllib.parse import urlparse
from urllib3.exceptions import MaxRetryError, LocationParseError

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
links_table = dynamodb.Table('Links')



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
            "Access-Control-Allow-Origin": "https://site.lilre.link"
        }
    else:
        response['headers'] = headers
        if 'Access-Control-Allow-Origin' not in response['headers']:
            response['headers']['Access-Control-Allow-Origin'] = "https://site.lilre.link"
    
    if body is not None:
        if not isinstance(body, str):
            body = json.dumps(body)
        response['body'] = body
    
    return response


def lambda_handler(event, context):
    logger.info(json.dumps(event))
    method = event['httpMethod']
    
    if method == 'GET':
        if event['resource'] !=  '/':
            id = event['pathParameters']['id']
            returned = links_table.get_item(Key={'id': id})
            if 'Item' not in returned:
                return generate_response(404, body={'details': 'Link not found.'})
            else:
                if event['resource'] == '/link/{id}':
                    return generate_response(200, body={'link': returned['Item']['link']})
                elif event['resource'] == '/{id}':
                    return generate_response(301, {'Location': returned['Item']['link']})
        elif event['resource'] == '/':
            return generate_response(301, {'Location': 'https://site.lilre.link'})
    elif method == 'POST':
        link = json.loads(event['body'])['link']
        
        if not good_to_create(link):
            return generate_response(412, body={'details': 'Link isn\'t valid or isn\'t live.'})
        
        id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        identity_hash = hash_dictionary(event['requestContext']['identity'])
        created_at = int(time.time())
        
        returned = links_table.put_item(Item={'id': id, 'link': link, 'identity_hash': identity_hash, 'created_at': created_at})
        return generate_response(200, body={'path': id})
    
    return generate_response(500, body={'details': 'Reached function end.'})
