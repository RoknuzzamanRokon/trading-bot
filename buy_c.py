import requests
import os
from dotenv import load_dotenv
import time


# Load API key and secret from environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY_1')
API_SECRET = os.getenv('API_SECRET_1')
API_PASSPHRASE = os.getenv('API_PASSPHRASE')

# Specify the product ID (e.g., 'BTC-USD' for Bitcoin to US Dollar)
product_id = 'BTC-USD'

# Function to get the current market price
def get_current_price(product_id):
    base_url = 'https://api.pro.coinbase.com'
    endpoint = f'/products/{product_id}/ticker'
    url = f'{base_url}{endpoint}'

    response = requests.get(url)
    if response.status_code == 200:
        return float(response.json()['price'])
    else:
        print(f"Failed to get current price. Status code: {response.status_code}, Response: {response.json()}")
        return None

# Function to place a market order
def place_market_order(product_id, side, funds):
    base_url = 'https://api.pro.coinbase.com'
    endpoint = '/orders'
    url = f'{base_url}{endpoint}'
    # Create a request header with the timestamp
    timestamp = str(time.time())

    # Set up the request headers
    headers = {
        'Content-Type': 'application/json',
        'CB-ACCESS-KEY': API_KEY,
        'CB-ACCESS-SIGN': 'signature_placeholder',
        'CB-ACCESS-TIMESTAMP': timestamp,
        'CB-ACCESS-PASSPHRASE': API_PASSPHRASE,
    }

    # Get the current market price
    current_price = get_current_price(product_id)
    if current_price is None:
        return

    # Calculate the size based on the funds
    size = funds / current_price

    # Set up the order parameters
    order_data = {
        'type': 'market',
        'side': side,   # 'buy' or 'sell'
        'product_id': product_id,
        'funds': funds,
    }

    # Make the request
    response = requests.post(url, json=order_data, headers=headers)

    # Check the response
    if response.status_code == 200:
        print(f"Market order placed successfully: {response.json()}")
    else:
        print(f"Failed to place market order. Status code: {response.status_code}, Response: {response.json()}")

# Example: Place a market buy order for $10
place_market_order(product_id, 'buy', 5)
