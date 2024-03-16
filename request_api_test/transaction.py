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
# 'f31a64bf-b49b-51ff-8ad6-2b12932fa63f'
    # Get buy and sell history
    transactions = client.get_transactions(account_id='47d9ebc3-2b6b-54a5-93a5-4d72dcb7e27a')  # Replace 'your_account_id' with the actual account ID
    print(transactions)
    #:account_id='47d9ebc3-2b6b-54a5-93a5-4d72dcb7e27a'
    # Print transaction history
    for transaction in transactions['data']:
        print("Transaction ID:", transaction['id'])
        print("Type:", transaction['type'])
        print("Title:", transaction['details']['title'])
        print("Header:", transaction['details']['header'])
        print("Health:", transaction['details']['health'])
        print("Subtitle:", transaction['details']['subtitle'])
      #  print("Fill price:", transaction['advanced_trade_fill']['fill_price'])
      #  print("Oreder Side:", transaction['advanced_trade_fill']['order_side'])
      #  print("Product Id:", transaction['advanced_trade_fill']['product_id'])
      #  print("Order Id:", transaction['advanced_trade_fill']['order_id'])


        print("Amount:", transaction['amount']['amount'], transaction['amount']['currency'])
        print("Timestamp:", transaction['created_at'])
        print("Status:", transaction['status'] )
        print("\n")

except Exception as e:
    print("API key is invalid. Error:", e)
