import ccxt
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# Initialize the Coinbase exchange
exchange = ccxt.coinbase({
    'apiKey': os.environ.get('API_KEY_5'),
    'secret': os.environ.get('API_SECRET_5'),
    'enableRateLimit': True,  # Enable rate limiting
})

# Fetch account information
def get_account_info():
    try:
        account_info = exchange.fetch_balance()
        print("Account Information:")
        for currency, balance in account_info['total'].items():
            print(f"{currency}: {balance}")
    except ccxt.NetworkError as e:
        print(f"Network Error: {e}")
    except ccxt.ExchangeError as e:
        print(f"Exchange Error: {e}")

# Call the function to get account information
get_account_info()

balance = exchange.fetch_balance()

# Print account balance
print(balance)


# Get trade history for the authenticated user
my_trades = exchange.fetch_my_trades('BTC/USD')
print(my_trades)



ticker = exchange.fetch_ticker('BTC/USD')
print(ticker)
