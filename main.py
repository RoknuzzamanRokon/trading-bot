import os
import requests
import time
from datetime import datetime, timedelta
from coinbase_advanced_trader.config import set_api_credentials
from coinbase_advanced_trader.strategies.fear_and_greed_strategies import trade_based_on_fgi_simple, fiat_limit_sell
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')


# Set API credentials for Coinbase Advanced Trader module
set_api_credentials(API_KEY, API_SECRET)

product_id = "BTC-USD"
btc_size = 10

symbol = 'BTC'
update_time = 1
running = True
max_buy = 1
max_sell = 1
sell_counter = 0
buy_counter = 0

PROFIT_PERCENTAGE = 2.0
LOSS_PERCENTAGE = 2.25

def get_coinbase_price(coin_symbol):
    api_key = API_KEY
    url = f'https://api.coinbase.com/v2/prices/{coin_symbol}-USD/spot'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        current_price = data['data']['amount']
        return current_price
    except Exception as e:
        print(f'Error: {str(e)}')
        return None

def get_last_day_closing_price(coin_symbol):
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

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if data:
            last_candle = data[-1]
            timestamp, low, high, open_price, close, volume = last_candle
            return close
        else:
            return f'No data available for the specified time range.'
    except Exception as e:
        return f'Error: {str(e)}'

def profit_amount(ia, pp):
    try:
        ia = float(ia) 
        profit_percentage_amount = (pp / 100) * ia
        total_profit_amount = ia + profit_percentage_amount
        return total_profit_amount
    except ValueError:
        print(f'Error converting ia to float in profit_amount')
        return None

def loss_amount(ia, lp):
    try:
        ia = float(ia) 
        loss_percentage_amount = (lp / 100) * ia
        total_loss_amount = ia - loss_percentage_amount 
        return total_loss_amount
    except ValueError:
        print(f'Error converting ia to float in loss_amount')
        return None
    

def lambda_handler(event, context):
    global buy_counter, sell_counter, running, max_buy, max_sell, update_time

    while running:
        print("-------------------------------------------------------")
        print(f"Total buy: {buy_counter} ")
        print(f"Total sell: {sell_counter} \n")

        closing_price_result = get_last_day_closing_price(coin_symbol=symbol)
        print(f"Closing price: {closing_price_result} \n")

        trade_buy_amount = loss_amount(closing_price_result, LOSS_PERCENTAGE)
        print(f"Buy Amount Point: {trade_buy_amount}")
        trade_sell_amount = profit_amount(closing_price_result, PROFIT_PERCENTAGE)
        print(f"Sell Amount Point: {trade_sell_amount} \n")

        update_price_result = get_coinbase_price(coin_symbol=symbol)
        print(f"Current Price: {update_price_result} \n")

        if update_price_result is not None:
            update_price_float = float(update_price_result)
            if buy_counter < max_buy and update_price_float <= trade_buy_amount:
                
                # trade_based_on_fgi_simple(product_id, btc_size) 
                print('~~~~~~~~~~~~~~~~~~~~~~Buy~~~~~~~~~~~~~~~~~~~~')
                buy_counter += 1

            elif sell_counter < max_sell and update_price_float >= trade_sell_amount:
                
                # fiat_limit_sell(product_id, btc_size)
                print('~~~~~~~~~~~~~~~~~~~~~Sell~~~~~~~~~~~~~~~~~~~~')
                sell_counter += 1

            elif sell_counter == max_sell and buy_counter == max_buy:
                running = False
        else:
            print('Skipping due to an error in obtaining the current price.')

        time.sleep(update_time)

# Uncomment the following line for local testing (not within AWS Lambda)
lambda_handler(None, None)