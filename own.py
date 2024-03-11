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

    # Choose the account where you want to place the market order
    account_id = accounts['data'][0]['id']  # Replace with your preferred account ID

    # Specify order details with account_id included
    order_params = {
        'funds': '10',  # Replace with the amount in USD you want to buy/sell
        'side': 'buy',  # 'buy' for buying, 'sell' for selling
        'product_id': 'BTC-USD',  # Replace with the trading pair you are interested in
        'type': 'market',  # Specify the order type as 'market'
        'account_id': account_id,  # Include the account_id parameter
    }

    # Place the market order
    order = client.create_order(**order_params)

    # Print order details
    print("Market Order Placed:")
    print(f"Order ID: {order['id']}")
    print(f"Status: {order['status']}")
    print(f"Side: {order['side']}")
    print(f"Funds: {order['funds']}")
    print(f"Time in Force: {order.get('time_in_force', 'N/A')}")

except Exception as e:
    print("API key is invalid or there was an error placing the order. Error:", e)
