import requests
from datetime import datetime, timedelta
import pandas as pd
from ta.momentum import RSIIndicator
import time

import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.environ.get('API_KEY')


def get_last_15_closing_prices(coin_symbol):
    api_key = API_KEY

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=14)
    
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    url = f'https://api.pro.coinbase.com/products/{coin_symbol}-USD/candles'
    params = {
        'start': start_time_iso,
        'end': end_time_iso,
        'granularity': 60
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        closing_prices = [candle[4] for candle in data]
        return closing_prices
    except Exception as e:
        return f'Error: {str(e)}'

def calculate_rsi(closing_prices, window_size):
    # Calculate RSI without pandas
    diff = [closing_prices[i] - closing_prices[i - 1] for i in range(1, len(closing_prices))]
    gain = [d if d > 0 else 0 for d in diff]
    loss = [-d if d < 0 else 0 for d in diff]

    avg_gain = sum(gain[:window_size]) / window_size
    avg_loss = sum(loss[:window_size]) / window_size

    for i in range(window_size, len(gain)):
        avg_gain = (avg_gain * (window_size - 1) + gain[i]) / window_size
        avg_loss = (avg_loss * (window_size - 1) + loss[i]) / window_size

    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Example usage:
coin_symbol = 'BTC'



while True:
    closing_prices = get_last_15_closing_prices(coin_symbol)
    print(closing_prices)
    
    if not isinstance(closing_prices, str): 
        window_size = 14  
        rsi = calculate_rsi(closing_prices, window_size)
        print(f'The RSI for the last 15 closing prices per minute is: {rsi}')
    else:
        print(closing_prices)


    time.sleep(5)