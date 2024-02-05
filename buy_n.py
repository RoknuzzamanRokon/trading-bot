import requests
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.environ.get('API_KEK')

# Set up logging
logging.basicConfig(level=logging.ERROR)

def get_last_day_closing_price(coin_symbol):
    try:
        api_key = API_KEY

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        start_time_iso = start_time.isoformat()
        end_time_iso = end_time.isoformat()

        url = f'https://api.pro.coinbase.com/products/{coin_symbol}-USD/candles'
        params = {
            'start': start_time_iso,
            'end': end_time_iso,
            'granularity': 3600
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()

        if data:
            last_candle = data[-1]
            timestamp, low, high, open_price, close, volume = last_candle
            return close
        else:
            return f'No data available for the specified time range.'
    except Exception as e:
        logging.error(f'Error in get_last_day_closing_price: {str(e)}')
        return None

def profit_amount(ia, pp):
    try:
        ia = float(ia)
        profit_percentage_amount = (pp / 100) * ia
        total_profit_amount = ia + profit_percentage_amount
        return total_profit_amount
    except ValueError:
        logging.error(f'Error converting ia to float in profit_amount')
        return None

def place_market_order(coin_symbol, amount_usd):
    try:
        api_key = API_KEY

        url = 'https://api.pro.coinbase.com/orders'
        
        # Calculate the quantity to buy based on the amount in USD and the last closing price
        last_closing_price = get_last_day_closing_price(coin_symbol)

        if last_closing_price is not None:
            quantity_to_buy = amount_usd / last_closing_price
        else:
            logging.error(f'Error: Unable to retrieve last closing price for {coin_symbol}')
            return None

        order_payload = {
            'type': 'market',
            'side': 'buy',
            'product_id': f'{coin_symbol}-USD',
            'funds': str(amount_usd),  # Specify funds for a market buy
            'size': str(quantity_to_buy)  # Specify size based on the calculated quantity
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        response = requests.post(url, headers=headers, json=order_payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        response_data = response.json()

        # Print the entire response for inspection
        print('Full Response:', response_data)

        return response_data

    except Exception as e:
        logging.error(f'Error placing market order: {str(e)}')
        return None

# Example: Place a market buy order for $10 worth of Bitcoin (BTC)
place_market_order('BTC', 10)
