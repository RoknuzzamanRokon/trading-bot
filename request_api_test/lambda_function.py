import requests
import os

def lambda_handler(event, context):
    url = 'https://zyv0q9hl1g.execute-api.us-east-2.amazonaws.com/config-stage/health'

    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"status code: {response.status_code}")

        return {
            'statusCode': response.status_code,
            'body': 'Success'
        }
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')

        return {
            'statusCode': 500,
            'body': 'Error'
        }