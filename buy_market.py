from coinbase_advanced_trader.strategies.market_order_strategies import fiat_market_buy
from coinbase_advanced_trader.config import set_api_credentials
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.environ.get('API_KEY_2')
API_SECRET = os.environ.get('API_SECRET_2')

# Set the API credentials
set_api_credentials(API_KEY, API_SECRET)

# Define the trading parameters
product_id = "BTC-USDC"  # Replace with your desired trading pair
btc_size = 10  # Replace with the amount of BTC you want to sell

# Perform a limit sell for just above the spot price of your desired trading pair
buy_order = fiat_market_buy(product_id, btc_size)
print("Limit Sell Order Response:", buy_order)