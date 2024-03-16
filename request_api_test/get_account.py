from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.environ.get('API_KEY_5')
api_secret = os.environ.get('API_SECRET_5')

# Initialize Coinbase client
client = Client(api_key, api_secret)

try:
    # Retrieve a list of all accounts
    accounts = client.get_accounts()

    # Print out the account IDs
    print("Account IDs:")
    for account in accounts['data']:
        print(f"Account Name: {account['name']}, Account ID: {account['id']}")
        
except Exception as e:
    print("Error:", e)

