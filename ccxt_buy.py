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
usd_amount = 10# Calculate the amount of BTC to buy for $10 at the limit price

# Load the markets.
exchange.load_markets()


ticker = exchange.fetch_ticker(symbol)
current_price = ticker['last']
amount = usd_amount / current_price

print(amount)
print(current_price)
print(ticker)

# Ensure the amount of BTC is within the exchange's limits and precision

amount = exchange.amount_to_precision(symbol, amount)
print(amount)
try:
    order = exchange.create_order(symbol, type, side, amount)
    print(order)
except Exception as e:
    print(f"An error occurred: {e}")
