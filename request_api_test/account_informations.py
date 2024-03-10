import requests
import hmac
import hashlib
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get('API_KEY_2')
API_SECRET = os.environ.get('API_SECRET_2')

def generate_signature(timestamp, method, request_path, body=''):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(API_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature

def get_account_info():
    timestamp = str(int(time.time()))
    method = 'GET'
    request_path = '/v2/accounts'  # Replace with the specific endpoint for account information
    signature = generate_signature(timestamp, method, request_path)

    headers = {
        'CB-ACCESS-KEY': API_KEY,
        'CB-ACCESS-SIGN': signature,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }

    url = 'https://api.coinbase.com' + request_path
    response = requests.get(url, headers=headers)

    return response.json()

account_info = get_account_info()
print(account_info)

