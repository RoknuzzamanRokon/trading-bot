import boto3
import json 
from custom_encoder import CustomEncoder
import botocore
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodbTableName = 'product-test'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodbTableName)

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'
healthPath = '/health'
productPath = '/product'
productsPath = '/products'


def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == getMethod and path == productPath:
        response = getProduct(event['queryStringParameters']['productId'])
    elif httpMethod == getMethod and path == productsPath:
        response = getProducts()
    elif httpMethod == postMethod and path == productPath:
        response = saveProduct(json.loads(event['body']))
    elif httpMethod == patchMethod and path == productPath:
        requestBody = json.loads(event['body'])
        response = modifyProduct(requestBody['productId'], requestBody['updateKey'], requestBody['updateValue'])
        
    elif httpMethod == deleteMethod and path == productPath:
        try:
            # Check if 'body' is not None
            if event['body'] is not None:
                requestBody = json.loads(event['body'])  # Convert JSON string to a Python dictionary
                if isinstance(requestBody, dict):
                    productId = requestBody.get('productId')
                    if productId is not None:
                        response = deleteProduct(productId)
                    else:
                        response = buildResponse(400, {'Message': 'productId is missing in the request body'})
                else:
                    response = buildResponse(400, {'Message': 'Invalid request body format'})
            else:
                response = buildResponse(400, {'Message': 'Request body is missing'})
        except json.JSONDecodeError:
            response = buildResponse(400, {'Message': 'Invalid JSON format in the request body'})
    


    else:
        response = buildResponse(404, 'Not Found')

    return response


def getProduct(productId):
    try:
        productId = int(productId)
        response = table.get_item(
            Key={
                'productId': productId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(400, {'Message': 'ProductId: %s not found' % productId})
    except botocore.exceptions.ClientError as e:
        # Log the specific exception details
        logger.exception('An error occurred: %s', e)
        return buildResponse(500, {'Message': 'Internal server error'})




def getProducts():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            result.extend(response['Items'])
        body = {
            'products': result
        }
        return buildResponse(200, body)
    except:
        logger.exception('Something')
    

def saveProduct(requestBody):
    try:
        table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body)
    except:
        logger.exception('Something')


def modifyProduct(productId, updateKey, updateValue):
    try:
        response = table.update_item(
            Key={
                'productId': productId
            },
            UpdateExpression = 'set %s = :value' % updateKey,
            ExpressionAttributeValues={
                ':value': updateValue
            },
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'UpdatedAttributes': response
        }
        return buildResponse(200, body)
    except:
        logger.exception('Something')


def deleteProduct(productId):
    try:
        productId = int(productId)
        response = table.delete_item(
            Key={
                'productId': productId
            },
            ReturnValues='ALL_OLD'
        )

        if 'Attributes' in response:
            # If 'Attributes' is present, it means an item was deleted, and you can access the old values
            deleted_item = response['Attributes']
            body = {
                'Operation': 'DELETE',
                'Message': 'SUCCESS',
                'DeletedItem': deleted_item
            }
            return buildResponse(200, body)
        else:
            # If 'Attributes' is not present, it means the item did not exist
            body = {
                'Operation': 'DELETE',
                'Message': 'SUCCESS',
                'DeletedItem': None  # Indicate that no item was deleted
            }
            return buildResponse(200, body)
            
    except ValueError:
        return buildResponse(400, {'Message': 'Invalid productId format'})
    except botocore.exceptions.ClientError as e:
        logger.exception('An error occurred: %s', e)
        return buildResponse(500, {'Message': 'Internal server error'})



def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers':{
            'Content-Type' : 'application/json',
            'Access-Control-Allow-Origin' : '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response