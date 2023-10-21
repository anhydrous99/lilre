import random
import string
import boto3
import json

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
links_table = dynamodb.Table('Links')


def lambda_handler(event, context):
    logger.info(event)
    method = event['httpMethod']
    if method == 'GET':
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
            else:
                return {
                    'statusCode': 301,
                    'headers': {
                        'Location': returned['Item']['link']
                    }
                }
    elif method == 'POST':
        link = json.loads(event['body'])['link']
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