from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.environ.get('API_KEY_2')
api_secret = os.environ.get('API_SECRET_2')

client = Client(api_key, api_secret)

try:
    user = client.get_current_user()
    print("API key is valid.")
    print(user)

    # Get buy and sell history
    transactions = client.get_transactions(account_id='f31a64bf-b49b-51ff-8ad6-2b12932fa63f')  # Replace 'your_account_id' with the actual account ID

    # Print transaction history
    for transaction in transactions['data']:
        print("Transaction ID:", transaction['id'])
        print("Type:", transaction['type'])
        print("Amount:", transaction['amount']['amount'], transaction['amount']['currency'])
        print("Timestamp:", transaction['created_at'])
        print("Status:", transaction['status'])
        print("\n")

except Exception as e:
    print("API key is invalid. Error:", e)
