from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.environ.get('API_KEY_5')
api_secret = os.environ.get('API_SECRET_5')

# Initialize Coinbase client
client = Client(api_key, api_secret)

def get_all_transactions(account_id):
    try:
        all_transactions = []

        # Initialize pagination parameters
        page = 1
        page_size = 25  # Adjust as needed

        while True:
            # Retrieve transactions for the specified account and page
            transactions = client.get_transactions(account_id, page=page, limit=page_size)
            all_transactions.extend(transactions['data'])

            # Check if there are more pages
            if len(transactions['data']) < page_size:
                break
            else:
                page += 1

        # Print out all transactions
        print("All Transactions for Account:", account_id)
        for transaction in all_transactions:
            print("Transaction ID:", transaction['id'])
            print("Type:", transaction['type'])
            print("Amount:", transaction['amount']['amount'], transaction['amount']['currency'])
            print("Timestamp:", transaction['created_at'])
            print("Status:", transaction['status'])
            print("\n")

    except Exception as e:
        print("Error:", e)# Replace 'your_account_id' with the actual account ID
account_id = '47d9ebc3-2b6b-54a5-93a5-4d72dcb7e27a'
get_all_transactions(account_id)

