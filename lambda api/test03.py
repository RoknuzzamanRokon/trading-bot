import boto3
import json
from custom_encoder import CustomEncoder
import logging
import botocore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodbTableName = 'customer-table'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodbTableName)

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'
healthPath = '/health'
customerPath = '/customer'
customersPath = '/customers'


def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == postMethod and path == customerPath:
        response = saveCustomer(json.loads(event['body']))
    elif httpMethod == getMethod and path == customerPath:
        response = getCustomer(event['queryStringParameters']['customerId'])
        
    else:
        response = buildResponse(400, {'message': 'Not Found'})
    
    return response


def getCustomer(customerId):
    try:
        customerId = int(customerId)
        response = table.get_item(
            Key={
                'customerId': customerId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % customerId})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle


def saveCustomer(requestBody):
    try:
        table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body=body)
    except Exception as e:
        logger.exception(f"{e}")
        body = {
            'Operation': 'SAVE',
            'Message': 'FAILED',
            'Error': str(e)
        }
        return buildResponse(500, body=body)


def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type' : 'application/json',
            'Access-Control-Allow-Origin' : '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response
