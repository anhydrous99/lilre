import logging
import boto3
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
links_table = dynamodb.Table('Links')

timeout_time = 2592000  # 30 Days in Seconds


def process_items(items):
    current_time = int(time.time())
    with links_table.batch_writer() as batch:
        for item in items:
            created_at = int(item['created_at'])
            if created_at + timeout_time < current_time:
                batch.delete_item(Key={'id': item['id']})


def lambda_handler(event, context):
    response = links_table.scan()

    if 'Items' in response:
        items = response['Items']
        process_items(items)
        time.sleep(.5)
        while 'LastEvaluatedKey' in response:
            response = links_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            if 'Items' in response:
                items = response['Items']
                process_items(items)
                time.sleep(.5)

    return {
        'statusCode': 200
    }
