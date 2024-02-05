import requests
import base64
import json
import time
import hmac
import hashlib
from dotenv import load_dotenv
import os

load_dotenv()


# Replace these with your own Coinbase Pro API credentials
api_key = os.environ.get('API_KEY')
api_secret =  os.environ.get('API_SECRET')
api_passphrase =  os.environ.get('API_PASSPHRASE')

# Replace these with your order details
product_id = 'BTC-USD'
desired_amount_usd = 10
desired_price = 39000  # Set your desired price per unit of cryptocurrency

# Coinbase Pro API endpoint
api_url = 'https://api.pro.coinbase.com'

# Function to create a Coinbase Pro API request
def create_api_request(method, endpoint, body=None):
    timestamp = str(time.time())
    message = f'{timestamp}{method}{endpoint}{body or ""}'
    signature = base64.b64encode(
        hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')

    headers = {
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-SIGN': signature,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'CB-ACCESS-PASSPHRASE': api_passphrase,
        'Content-Type': 'application/json'
    }

    return headers

# Function to place a limit order
def place_limit_order(product_id, desired_amount_usd, desired_price):
    try:
        endpoint = '/orders'
        method = 'POST'
        body = {
            'type': 'limit',
            'side': 'buy',
            'product_id': product_id,
            'size': str(desired_amount_usd),
            'price': str(desired_price),
            'time_in_force': 'GTC'  # Good 'til canceled
        }

        api_request = create_api_request(method, endpoint, json.dumps(body))
        response = requests.post(api_url + endpoint, headers=api_request, data=json.dumps(body))

        # Debugging information
        print(f"Request Headers: {api_request}")
        print(f"Request Body: {json.dumps(body)}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        response.raise_for_status()  # Check for HTTP errors

        return response.json()

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")


# Place the limit order
response = place_limit_order(product_id, desired_amount_usd, desired_price)

# Print the response
print(json.dumps(response, indent=2))