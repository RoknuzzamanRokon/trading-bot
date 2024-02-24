from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY')
api_secret = os.environ.get('API_SECRET')

client = Client(api_key, api_secret)

try:
    user = client.get_current_user()
    print("API key is valid.")
    print(user)

    print(user['country'])
    print(user['country']['is_in_europe'])
except Exception as e:
    print("API key is invalid. Error:", e)  