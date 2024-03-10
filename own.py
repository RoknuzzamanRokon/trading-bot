import requests
import time
import hashlib
import hmac
from enum import Enum

class Method(Enum):
    GET = 'GET'
    POST = 'POST'

def get_latest_price(product_id):
    base_url = 'https://api.pro.coinbase.com'
    endpoint = f'/products/{product_id}/ticker'
    
    url = f'{base_url}{endpoint}'
    response = requests.get(url)
    
    try:
        response_json = response.json()
        latest_price = response_json.get('price', None)
        return float(latest_price) if latest_price else None
    except ValueError:
        print("Response Content:", response.content.decode('utf-8'))
        return None

def place_market_buy_order(api_key, api_secret, product_id, usd_amount):
    base_url = 'https://api.pro.coinbase.com'
    endpoint = '/orders'
    
    timestamp = str(int(time.time()))
    message = f'{timestamp}{Method.POST.value}{endpoint}'
    signature = hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    headers = {
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-SIGN': signature,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'Content-Type': 'application/json',
    }

    latest_price = get_latest_price(product_id)
    
    if latest_price:
        # Calculate the equivalent BTC amount based on the USD amount and the latest price
        btc_amount = usd_amount / latest_price

        order_data = {
            'size': str(btc_amount),
            'side': 'buy',
            'product_id': product_id,
            'type': 'market',  # Set order type to 'market' for a market order
        }

        url = f'{base_url}{endpoint}'
        response = requests.post(url, headers=headers, json=order_data)
        
        try:
            response_json = response.json()
            print("Buy Order Response:", response_json)
            return response_json
        except ValueError:
            print("Response Content:", response.content.decode('utf-8'))
            return None

    return None

# Example usage
api_key = ''
api_secret = ''
product_id = 'BTC-USD'
usd_amount_to_spend = 10.0

try:
    market_buy_order_response = place_market_buy_order(api_key, api_secret, product_id, usd_amount_to_spend)
    print("Market Buy Order Response:")
    print(market_buy_order_response)
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'response') and e.response is not None:
        print("Detailed Response:")
        print("Status Code:", e.response.status_code)
        print("Headers:", e.response.headers)
        print("Response Content:", e.response.content.decode('utf-8'))