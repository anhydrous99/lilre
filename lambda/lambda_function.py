import random
import string
import boto3
import json

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


def lambda_handler(event, context):
    logger.info(event)
    method = event['httpMethod']
    if method == 'GET':
        if event['path'] != '/':
            id = event['pathParameters']['id']
            returned = links_table.get_item(Key={'id': id})
            if 'Item' not in returned:
                return {
                    'statusCode': 404,
                    'headers': {"Content-Type": "application/json"},
                    'body': json.dumps({'details': 'Link not found.'})
                }
            else:
                if event['requestContext']['resourcePath'] == '/link/{id}':
                    return {
                        'statusCode': 200,
                        'headers': {"Content-Type": "application/json"},
                        'body': json.dumps({'link': returned['Item']['link']})
                    }
                elif event['requestContext']['resourcePath'] == '{id}':
                    return {
                        'statusCode': 301,
                        'headers': {
                            'Location': returned['Item']['link']
                        }
                    }
        else:
            return {
                'statusCode': 301,
                'headers': {
                    'Location': 'http://site.lilre.link'
                }
            }
    elif method == 'POST':
        link = json.loads(event['body'])['link']
        
        if not good_to_create(link):
            return {
                'statusCode': 412,
                'headers': {"Content-Type": "application/json"},
                'body': json.dumps({'details': 'Link isn\'t valid or isn\'t live.'})
            }
        
        id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        returned = links_table.put_item(Item={'id': id, 'link': link})
        return {
            'statusCode': 200,
            'headers': {"Content-Type": "application/json"},
            'body': json.dumps({'path': id})
        }
    return {
        'statusCode': 500
    }