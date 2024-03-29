from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY_5')
api_secret = os.environ.get('API_SECRET_5')

client = Client(api_key, api_secret)



try:
    # Get all accounts
    accounts = client.get_accounts()
    print(accounts)

    # Loop through each account and print address information
    for account in accounts['data']:
        print(f"Account Name: {account['name']}, Account ID: {account['id']}, Blance: {account['balance']['amount']} {account['balance']['currency']}")
        addresses = client.get_addresses(account['id'])

except Exception as e:
    print("Error:", e)
