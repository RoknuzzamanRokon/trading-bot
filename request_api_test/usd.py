from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY_2')
api_secret = os.environ.get('API_SECRET_2')

client = Client(api_key, api_secret)

try:
    # Get all accounts
    accounts = client.get_accounts()

    # Find the USD wallet account
    usd_account = next((account for account in accounts['data'] if account['currency'] == 'AMP'), None)

    if usd_account:
        # Print USD balance
        print("USD Balance:", usd_account['balance']['amount'])
    else:
        print("USD wallet not found.")

except Exception as e:
    print("Error:", e)

