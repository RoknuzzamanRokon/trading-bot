import os
import requests
import time
from datetime import datetime, timedelta
from coinbase_advanced_trader.config import set_api_credentials
from coinbase_advanced_trader.strategies.fear_and_greed_strategies import trade_based_on_fgi_simple, fiat_limit_sell
from dotenv import load_dotenv
import boto3

dynamodb = boto3.client('dynamodb')
table_name = 'buy_counter_table'

load_dotenv()
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')
set_api_credentials(API_KEY, API_SECRET)


product_id = "ETH-USD"
USD_Size = 10
symbol = 'ETH'

max_buy = 3
max_sell = 3

PROFIT_PERCENTAGE = 0.71
LOSS_PERCENTAGE = 0.70




update_time = 5
btc_size = int(USD_Size)
running = True
sell_counter = 0
buy_counter = 0
window_size = 8
window_size_for_rsi = 14 

buy_counter_db = 0



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
    start_time = end_time - timedelta(minutes=15)
    
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    url = f'https://api.pro.coinbase.com/products/{coin_symbol}-USD/candles'
    params = {
        'start': start_time_iso,
        'end': end_time_iso,
        'granularity': 900  
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
    

def get_last_month_prices(coin_symbol):
    api_key = API_KEY

    end_time = datetime.utcnow()
    
    start_time = end_time - timedelta(days=30)
    
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    url = f'https://api.pro.coinbase.com/products/{coin_symbol}-USD/candles'
    params = {
        'start': start_time_iso,
        'end': end_time_iso,
        'granularity': 86400
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        return data
    except Exception as e:
        return f'Error: {str(e)}'


def calculate_moving_average(prices, window_size):
    closing_prices = [candle[4] for candle in prices]
    moving_average = sum(closing_prices[-window_size:]) / window_size
    return moving_average



def get_last_60_closing_prices(coin_symbol):
    api_key = API_KEY

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    url = f'https://api.pro.coinbase.com/products/{coin_symbol}-USD/candles'
    params = {
        'start': start_time_iso,
        'end': end_time_iso,
        'granularity': 60  # Set granularity to 60 seconds (1 minute)
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
    

def decide_trade_action(rsi_value):
    if rsi_value > 70:
        return "Sell"
    elif rsi_value < 30:
        return "Buy"
    else:
        return "Hold"
    

# Database Connection.
dynamodb = boto3.resource('dynamodb')
table_name = 'artmix_tb4_table_01'
table = dynamodb.Table(table_name)

def get_buy_counter():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('buy_counter')
    except Exception as e:
        print(f"Error retrieving buy counter: {e}")
        return 0
        
        
def get_sell_counter():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('sell_counter', 0)
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0


def get_buy_price():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('buy_price')
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0
        
        
def get_sell_price():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('sell_price')
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0
    
def get_total_buy():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('total_buy')
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0
    
def get_total_sell():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('total_sell')
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0
    

def update_buy_sell_counter(buy_count,sell_count,total_buy,total_sell):
    data_to_insert = {
            'counter_id': 1, 
            'buy_counter': int(buy_count),
            'sell_counter': int(sell_count),
            'total_buy': int(total_buy),
            'total_sell': int(total_sell)
        }
        
    try:
        # Insert or update data into DynamoDB
        response = table.put_item(Item=data_to_insert)
        return response
    except Exception as e:
        print(f"Error updating buy counter: {e}")
        return None


def lambda_handler(event, context):
    global buy_counter, sell_counter, running, max_buy, max_sell, update_time, buy_counter_db, window_size_for_rsi
    
    buy_check = get_buy_counter()
    sell_check = get_sell_counter()
    
    while running:
        print("----------------------------------------------------------------------------")
        # print(f"Total buy: {buy_counter} ")
        # print(f"Total sell: {sell_counter} \n")
        buy_check = get_buy_counter()
        print("Get data form db buy:", buy_check)
        sell_check = get_sell_counter()
        print("Get data form db sell:", sell_check)
        
        total_buy = get_total_buy()
        print(f"Total buy: {total_buy}")
        total_sell = get_total_sell()
        print(f"Total sell: {total_sell}")
        
        historical_prices = get_last_month_prices(symbol)
        moving_average = calculate_moving_average(historical_prices, window_size)
        print(f'Moving Average: {moving_average}')

        closing_price_result = get_last_day_closing_price(coin_symbol=symbol)
        print(f"Closing price: {closing_price_result} \n")

        trade_buy_amount = loss_amount(closing_price_result, LOSS_PERCENTAGE)
        print(f"Buy Amount Point: {trade_buy_amount}")
        trade_sell_amount = profit_amount(closing_price_result, PROFIT_PERCENTAGE)
        print(f"Sell Amount Point: {trade_sell_amount} \n")

        update_price_result = get_coinbase_price(coin_symbol=symbol)
        print(f"Current Price: {update_price_result} \n")
        
        
        closing_prices = get_last_60_closing_prices(coin_symbol=symbol)
    

        if not isinstance(closing_prices, str):
            
            rsi = calculate_rsi(closing_prices, window_size_for_rsi)
            print(f'The RSI for the result candle prices per minute is: {rsi}')
        
        
        if update_price_result is not None:
            update_price_float = float(update_price_result)
            if buy_counter < max_buy and total_buy <= max_buy and rsi <= 30 and buy_check == 0:
                
                # trade_based_on_fgi_simple(product_id, btc_size)

                print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Buy~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~') 
                buy_counter += 1

                total_buy += 1
                total_sell += 0
                
                # Calculate sell price.
                # sell_price = profit_amount(buy_price, PROFIT_PERCENTAGE)
                # print(f"Sell Price: {sell_price}")

                set_buy = 1
                set_sell = 0
                update_buy_sell_counter(set_buy, set_sell, total_buy, total_sell)
                # update_buy_sell_counter(set_buy, set_sell,buy_price,sell_price)


            # elif sell_counter < max_sell and total_buy <= max_buy and rsi >= 70:
                
            #     fiat_limit_sell(product_id, btc_size)
            #     print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Sell~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            #     sell_counter += 1

            #     reset_buy = 0
            #     reset_sell = 0
            #     update_buy_sell_counter(reset_buy, reset_sell)


            elif sell_counter < max_sell and rsi >= 70 and total_sell <= max_sell and buy_check > 0:
                
                # fiat_limit_sell(product_id, btc_size)
                print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Sell~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                sell_counter += 1

                total_buy += 0
                total_sell += 1

                reset_buy = 0
                reset_sell = 0
                update_buy_sell_counter(reset_buy, reset_sell, total_buy, total_sell)



            elif sell_counter == max_sell and buy_counter == max_buy:
                running = False
        else:
            print('Skipping due to an error in obtaining the current price.')

        time.sleep(update_time)


