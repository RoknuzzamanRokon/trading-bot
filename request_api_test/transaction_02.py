from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.environ.get('API_KEY_5')
api_secret = os.environ.get('API_SECRET_5')


client = Client(api_key, api_secret)

try:
    # Get a list of all accounts
    accounts = client.get_accounts()

    # Loop through each account and fetch its transaction history
    for account in accounts['data']:
        account_id = account['id']
        transactions = client.get_transactions(account_id)

        # Print transaction details for this account
        print(f"Transactions for account '{account['name']}' (ID: {account_id}):")
        for transaction in transactions['data']:
            print("Transaction ID:", transaction['id'])
            print("Type:", transaction['type'])
            print("Amount:", transaction['amount']['amount'], transaction['amount']['currency'])
            print("Timestamp:", transaction['created_at'])
            print("Status:", transaction['status'])
            print("\n")

except Exception as e:
    print("Error:", e)
