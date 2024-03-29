import ccxt
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('API_KEY_1')
api_secret = os.getenv('API_SECRET_1')
exchange = ccxt.coinbasepro({
    'apiKey': api_key,
    'secret': api_secret,
})

symbol = 'BTC/USD'
type = 'market'  # Type of order
side = 'buy'  # Buying BTC
amount = 10# Calculate the amount of BTC to buy for $10 at the limit price

amount = usd_amount / limit_price

# Ensure the amount of BTC is within the exchange's limits and precision
market = exchange.market(symbol)
amount = exchange.amount_to_precision(symbol, amount)

try:
    order = exchange.create_order(symbol, type, side, amount, limit_price)
    print(order)
except Exception as e:
    print(f"An error occurred: {e}")
