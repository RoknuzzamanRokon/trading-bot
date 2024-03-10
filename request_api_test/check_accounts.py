from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY_2')
api_secret = os.environ.get('API_SECRET_2')

client = Client(api_key, api_secret)

try:
    # Get account IDs
    accounts = client.get_accounts()
    # Print account IDs
    print("Account IDs:")
    for account in accounts['data']:
        print(f"Account Name: {account['name']}, Account Id: {account['id']}, Balance: {account['balance']['amount']},Currency: {account['balance']['currency']}")

except Exception as e:
    print("API key is invalid. Error:", e)
