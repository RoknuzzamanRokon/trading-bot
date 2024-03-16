from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY_5')
api_secret = os.environ.get('API_SECRET_5')

client = Client(api_key, api_secret)

try:
    user = client.get_current_user()
    print("API key is valid.")
    print(user)

    print(user['country'])
    print(user['country']['is_in_europe'])

    # Get account IDs
    accounts = client.get_accounts()
    print(accounts)
    # Print account IDs
    print("Account IDs:")
    for account in accounts['data']:
        print(account['id'])

except Exception as e:
    print("API key is invalid. Error:", e)  
