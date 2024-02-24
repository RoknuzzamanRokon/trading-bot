import os
import json
import time
import boto3
import logging
import botocore
import requests
from decimal import Decimal
from custom_encoder import CustomEncoder
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coinbase_advanced_trader.config import set_api_credentials
from coinbase_advanced_trader.strategies.fear_and_greed_strategies import trade_based_on_fgi_simple, fiat_limit_sell, fiat_limit_buy
from boto3.dynamodb.conditions import Attr,Key
import math
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from coinbase.wallet.client import Client


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variable section.
# load_dotenv()
# API_KEY = os.environ.get('API_KEY')
# API_SECRET = os.environ.get('API_SECRET')


# Database Connection.
dynamodb = boto3.resource('dynamodb')
table_1 = 'customer-counter-table'
table = dynamodb.Table(table_1)

table_2 = 'customer-table'
customer_table = dynamodb.Table(table_2)

table_3 = 'order-configuration-table'
order_configuration_table = dynamodb.Table(table_3)

table_4 = 'bot-output-table'
bot_output_table = dynamodb.Table(table_4)

table_5 = 'valid-customer-table'
valid_customer_table = dynamodb.Table(table_5)




update_time = 1
window_size = 30
window_size_for_rsi = 14 

buy_counter_db = 0


def checkValidApiKey(api_key):

    url = 'https://api.coinbase.com/v2/user'

    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}',
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 

        if 'data' in response.json() and 'id' in response.json()['data']:
            print('API key is valid!')
        else:
            print('API key is not valid.')

    except requests.exceptions.HTTPError as err:
        print(f'HTTP error occurred: {err}')
    except Exception as e:
        print(f'An error occurred: {e}')


def getCoinMarketCap():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    parameters = {
    'start':'1',
    'limit':'10',
    'convert':'USD'
    }

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '2ce8972a-2751-4b3d-ab17-2e2cfd8a1a04',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)



def get_coinbase_price(coin_symbol, api_key):
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



def get_last_day_closing_price(coin_symbol, api_key):
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
    
def get_last_month_prices(coin_symbol, api_key):
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

def get_last_60_closing_prices(coin_symbol, api_key):
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
    
def valid_customer(customerId, is_valid, is_in_europe, api_key, api_secret):
    data_to_insert = {
        'customerId': str(customerId),
        'is_valid': bool(is_valid),
        'is_in_europe': bool(is_in_europe),
        'api_key': str(api_key),
        'api_secret': str(api_secret)
    }
    try:
        response = valid_customer_table.put_item(Item=data_to_insert)
        return response
    except Exception as e:
        print(f'Error updating valid customer: {e}')
        return None
    

def update_buy_sell_counter(customerId,buy_count,sell_count,total_buy,total_sell,current_price,last_buySell_status):
    data_to_insert = {
            'counter_id': str(customerId), 
            'buy_counter': int(buy_count),
            'sell_counter': int(sell_count),
            'total_buy': int(total_buy),
            'total_sell': int(total_sell),
            'current_price': Decimal(current_price),
            'last_buySell_status':str(last_buySell_status)
        }
        
    try:
        # Insert or update data into DynamoDB
        response = table.put_item(Item=data_to_insert)
        return response
    except Exception as e:
        print(f"Error updating buy sell counter: {e}")
        return None


def update_configuration_table(customerId,symbol,usd_size,product_id,max_buy,max_sell,PROFIT_PERCENTAGE, LOSS_PERCENTAGE, isSubmitted):
    data_to_insert = {
            'customerId': str(customerId), 
            'symbol': str(symbol),
            'usd_size': Decimal(usd_size),
            'product_id': str(product_id),
            'max_buy': Decimal(max_buy),
            'max_sell': Decimal(max_sell),
            'PROFIT_PERCENTAGE': str(PROFIT_PERCENTAGE),
            'LOSS_PERCENTAGE': str(LOSS_PERCENTAGE),
            'isSubmitted': bool(isSubmitted)
        }
        
    try:
        # Insert or update data into DynamoDB
        response = order_configuration_table.put_item(Item=data_to_insert)
        return response
    except Exception as e:
        print(f"Error updating buy sell counter: {e}")
        return None
    
    
def update_bot_output(customerId, moving_average, closing_price_result, update_price_result, trade_buy_amount, trade_sell_amount, rsi, symbol):
    data_to_insert = {
        'display_id': str(customerId),
        'moving_average_price': Decimal(str(moving_average)),
        'closing_price_result': Decimal(str(closing_price_result)),
        'update_price_result': str(update_price_result),
        'trade_buy_amount': Decimal(str(trade_buy_amount)),
        'trade_sell_amount': Decimal(str(trade_sell_amount)),
        'rsi_value': Decimal(str(rsi)),
        'symbol': str(symbol)
    }
    try:
        response = bot_output_table.put_item(Item=data_to_insert)
        return response
    except Exception as e:
        print(f"Error updating bot output {e}")
        return None

def get_buy_counter(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('buy_counter')
    except Exception as e:
        print(f"Error retrieving buy counter: {e}")
        return 0
        
def get_sell_counter(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('sell_counter', 0)
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0

def get_buy_price(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('buy_price')
    except Exception as e:
        print(f"Error retrieving buy counter: {e}")
        return 0
    
def get_sell_price(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('sell_price')
    except Exception as e:
        print(f"Error retrieving sell counter: {e}")
        return 0
    
def get_total_buy(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('total_buy')
    except Exception as e:
        print(f"Error retrieving total buy counter: {e}")
        return 0
    
def get_total_sell(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('total_sell')
    except Exception as e:
        print(f"Error retrieving total sell counter: {e}")
        return 0
        
def get_current_price(customerId):
    try:
        customerId = str(customerId)
        response = table.get_item(Key={'counter_id': customerId})
        item = response.get('Item', {})
        return item.get('current_price')
    except Exception as e:
        print(f"Error retrieving current price: {e}")
        return 0
    
running = True


def lambda_handler(event, context):
    global update_time, buy_counter_db, window_size_for_rsi, window_size, running

    
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']


    # Scan the table to retrieve all customer IDs
    response = customer_table.scan(ProjectionExpression='customerId')
    # Extract and print the customer IDs
    customer_ids = [item['customerId'] for item in response.get('Items', [])]


    # Scan the configuration table to retrieve all customer IDs
    response_for_configuration_table = order_configuration_table.scan(ProjectionExpression='customerId')
    configuration_customer_ids = [item['customerId'] for item in response_for_configuration_table.get('Items', [])]

    if customer_ids:
        print("Customer IDs:")
        for customer_id in customer_ids:
            print(f"***********************------------------CustomerId:{customer_id}")

            api_key = getCustomerItem(customerId=customer_id, attributeToSearch='apiKey')
            if 'body' in api_key:
                api_key_body = api_key['body']
                api_key_body_strip = api_key_body.strip('\"')

            api_secret = getCustomerItem(customerId=customer_id, attributeToSearch='apiSecret')
            if 'body' in api_secret:
                api_secret_body = api_secret['body']
                api_secret_body_strip = api_secret_body.strip('\"')

            # Client validation check here.
            client_validation_check = Client(api_key_body_strip, api_secret_body_strip)

            try:
                user_check = client_validation_check.get_current_user()
                print("API key is valid.")

                check_europe = user_check['country']['is_in_europe']
                is_valid = True,
                is_in_europe = check_europe                
                valid_customer(customerId=customer_id, is_valid=is_valid, is_in_europe=is_in_europe, api_key=api_key_body_strip, api_secret=api_secret_body_strip)
            
            except Exception as e:
                print("API key is invalid. Error:", e)


            if customer_id not in configuration_customer_ids: 
                    customerId=customer_id
                    symbol="BTC"
                    usd_size=0
                    product_id="BTC-USD"
                    max_buy=0
                    max_sell=0
                    PROFIT_PERCENTAGE="1.0"
                    LOSS_PERCENTAGE="1.0"
                    isSubmitted = True
                    update_configuration_table(customerId,symbol, usd_size, product_id, max_buy, max_sell, PROFIT_PERCENTAGE, LOSS_PERCENTAGE, isSubmitted)

            
            
            

                
            running_status = getCustomerItem(customerId=customer_id, attributeToSearch='running_status')
            if 'body' in running_status:
                running_status_body = running_status['body']
                running_status_body_strip = running_status_body.strip('\"')

                print(f"Running Status: {running_status_body_strip}")
                # print(running_status_body_strip)
                # print(type(running_status_body_strip))


                # if running_status_body_strip == "ON":
                #     print("present")
                # else:
                #     print("Not present")

            symbol_01 = getOrderConfig(customerId=customer_id, attributeToSearch='symbol')
            if 'body' in symbol_01:
                symbol_str = symbol_01['body']
                symbol_str_strip = symbol_str.strip('\"')

            product_id_01 = getOrderConfig(customerId=customer_id, attributeToSearch='product_id')
            if 'body' in product_id_01:
                symbol_str = product_id_01['body']
                product_id_str_strip = symbol_str.strip('\"')

            profit_count = getOrderConfig(customerId=customer_id, attributeToSearch='PROFIT_PERCENTAGE')
            if 'body' in profit_count:
                symbol_str = profit_count['body']
                profit_count_strip = symbol_str.strip('\"')
                print(f"profit profit check into db:---------------{profit_count_strip}")
                print(type(profit_count_strip))
                profit_count_strip_int = float(profit_count_strip)
                print(type(profit_count_strip_int))
                

            loss_count = getOrderConfig(customerId=customer_id, attributeToSearch='LOSS_PERCENTAGE')
            if 'body' in loss_count:
                symbol_str = loss_count['body']
                loss_count_strip = symbol_str.strip('\"')
                loss_count_strip_int = float(loss_count_strip)
                print(type(loss_count_strip_int))
                print(f"Loss profit check into db:---------------{loss_count_strip_int}")

            max_buy_count = getOrderConfig(customerId=customer_id, attributeToSearch='max_buy')
            if 'body' in max_buy_count:
                symbol_str = max_buy_count['body']
                max_buy_count_strip = symbol_str.strip('\"')
                float_max_buy_count_strip = float(max_buy_count_strip)
                print(type(loss_count_strip_int))
                print(f"Loss profit check into db:---------------{loss_count_strip_int}")

            max_sell_count = getOrderConfig(customerId=customer_id, attributeToSearch='max_sell')
            if 'body' in max_sell_count:
                symbol_str = max_sell_count['body']
                max_sell_count_strip = symbol_str.strip('\"')
                float_max_sell_count_strip = float(max_sell_count_strip)


            max_buy = float_max_buy_count_strip
            max_sell = float_max_sell_count_strip


            USD_Size = getOrderConfig(customerId=customer_id, attributeToSearch='usd_size')
            if 'body' in USD_Size:
                symbol_str = USD_Size['body']
                USD_Size_strip = symbol_str.strip('\"')


            buy_check = get_buy_counter(customerId=customer_id)
            print(f"THis is sell check: {buy_check}")
            sell_check = get_sell_counter(customerId=customer_id)
            print(f"THis is sell check: {sell_check}")
            
            

            # Add logic for entering trad.
            if running_status_body_strip == "ON": 
                symbol = symbol_str_strip
                product_id = product_id_str_strip
                
                USD_Size = float(USD_Size_strip)
                print(f"USD SIZE: {USD_Size}")
                btc_size = float(USD_Size)
                sell_btc_size = btc_size + 0.06


                print("----------------------------------------------------------------------------")
                print(f"Hey, I'm {product_id} here.")
                buy_check = get_buy_counter(customerId=customer_id)
                print("Get data form db buy:", buy_check)
                sell_check = get_sell_counter(customerId=customer_id)
                print("Get data form db sell:", sell_check)
                
                total_buy = get_total_buy(customerId=customer_id)
                print(f"Total buy: {total_buy}")
                total_sell = get_total_sell(customerId=customer_id)
                print(f"Total sell: {total_sell}")
                
                if buy_check is None: 
                    customerId=customer_id
                    set_buy=0
                    set_sell=0
                    total_buy=0
                    total_sell=0
                    current_price=0
                    last_buySell_status='-'
                    update_buy_sell_counter(customerId,set_buy, set_sell, total_buy, total_sell, current_price, last_buySell_status)
            
                get_current_price_db = get_current_price(customerId=customer_id)
                print(type(get_current_price_db))
                print(f"Get current price in DB: {get_current_price_db}")
                
                historical_prices = get_last_month_prices(symbol, api_key=api_key_body_strip)
                # print(f"last month price: {historical_prices}")
                # print(type(historical_prices))
                moving_average = calculate_moving_average(historical_prices, window_size)
                print(f'Moving Average: {moving_average}')

                closing_price_result = get_last_day_closing_price(coin_symbol=symbol, api_key=api_key_body_strip)
                print(f"Closing price: {closing_price_result} \n")
                
                update_price_result = get_coinbase_price(coin_symbol=symbol, api_key=api_key_body_strip)
                print(f"Current Price: {update_price_result} \n")


                profit_amount_default = 1.0
                loss_amount_default = 1.0


                trade_buy_amount = loss_amount(closing_price_result, loss_amount_default)
                print(type(trade_buy_amount))
                print(f"Buy Amount Price: {trade_buy_amount}")
                
                if buy_check == 0:
                    trade_sell_amount = profit_amount(closing_price_result, profit_amount_default)
                    print(f"Sell Amount Price: {trade_sell_amount} \n")
                    
                else:
                    trade_sell_amount = profit_amount(get_current_price_db, profit_amount_default)
                    print(f"Sell Amount Price: {trade_sell_amount} \n")
                    
                closing_prices = get_last_60_closing_prices(coin_symbol=symbol, api_key=api_key_body_strip)
                print(f"get_last_60_closing_prices: {closing_prices}")
                if not isinstance(closing_prices, str):
                    
                    rsi = calculate_rsi(closing_prices, window_size_for_rsi)
                    print(f'The RSI for the result candle prices per minute is: {rsi}')
                
                customerId = customer_id
                # Rounded all value in 2 decimal places.
                round_moving_average = round(moving_average, 2)
                round_closing_price_result = round(closing_price_result, 2)
                round_trade_buy_amount = round(trade_buy_amount, 2)
                round_trade_sell_amount = round(trade_sell_amount, 2)
                round_rsi = round(rsi, 2)
                
                # Bot output update in database.
                update_bot_output(customerId=customerId, moving_average=round_moving_average, closing_price_result=round_closing_price_result,
                                update_price_result=update_price_result, trade_buy_amount=round_trade_buy_amount, 
                                trade_sell_amount=round_trade_sell_amount, rsi=round_rsi, symbol=symbol)
                
                
                set_api_credentials(api_key_body_strip, api_secret_body_strip)

                if update_price_result is not None:
                    update_price_float = float(update_price_result)
                    if total_buy < max_buy and rsi <= 30 and buy_check == 0 and trade_buy_amount + 200 >= current_price:
                        
                        # fiat_limit_buy(product_id, btc_size)

                        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Buy~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~') 
                        total_buy += 1
                        total_sell += 0
                        
                        current_price = get_coinbase_price(coin_symbol=symbol, api_key=api_key_body_strip)
                        print(f"Get current price from coinbase: {current_price}")
                        print(type(current_price))

                        set_buy = 1
                        set_sell = 0

                        customerId = customer_id

                        last_buySell_status = 'Buy'

                        update_buy_sell_counter(customerId=customerId, buy_count=set_buy, sell_count=set_sell, total_buy=total_buy, total_sell=total_sell, current_price=current_price, last_buySell_status=last_buySell_status)
                    

                    elif total_sell < max_sell and buy_check > 0 and trade_sell_amount <= update_price_float and rsi >= 50:
                        
                        # fiat_limit_sell(product_id, sell_btc_size)
                        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Sell~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                        sell_counter += 1

                        total_buy += 0
                        total_sell += 1

                        reset_buy = 0
                        reset_sell = 0
                        reset_current_price = 0

                        customerId = customer_id         

                        last_buySell_status = 'sell'
                        update_buy_sell_counter(customerId=customerId, buy_count=reset_buy, sell_count=reset_sell, total_buy=total_buy, total_sell=total_sell, current_price=reset_current_price, last_buySell_status=last_buySell_status)

                else:
                    print('Skipping due to an error in obtaining the current price.')

            elif running_status_body_strip == "OFF":
                print(f'Hey my running status is of: {running_status_body}')

                customerId=customer_id
                set_buy=0
                set_sell=0
                total_buy=0
                total_sell=0
                current_price_set_value=0
                last_buySell_status='-'
                update_buy_sell_counter(customerId,set_buy, set_sell, total_buy, total_sell, current_price_set_value, last_buySell_status)
        

                
                moving_average = 0
                closing_price_result = 0
                update_price_result = "0"
                trade_buy_amount = 0
                trade_sell_amount = 0
                rsi = 0
                symbol = 'null'

                update_bot_output(customerId=customerId, moving_average=moving_average, closing_price_result=closing_price_result,
                                update_price_result=update_price_result, trade_buy_amount=trade_buy_amount, 
                                trade_sell_amount=trade_sell_amount, rsi=rsi, symbol=symbol)

    else:
        print("No customer IDs found in the table.")



    # This is API section. 
    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == postMethod and path == customerPath:
        response = saveCustomer(json.loads(event['body']))
    elif httpMethod == getMethod and path == customerPath:
        response = getCustomer(event['queryStringParameters']['customerId'])
    elif httpMethod == getMethod and path == customerItemPath:
        response = getCustomerItem(event['queryStringParameters']['customerId'], event['queryStringParameters']['attributeToSearch'])    
    elif httpMethod == patchMethod and path == customerPath:
        requestBody = json.loads(event['body'])
        response = modifyCustomerInfo(requestBody['customerId'], requestBody['updateKey'], requestBody['updateValue'])

    elif httpMethod == postMethod and path == orderConfigPath:
        response = saveOrderConfig(json.loads(event['body']))
    elif httpMethod == getMethod and path == orderConfigPath:
        response = getOrderConfig(event['queryStringParameters']['customerId'], event['queryStringParameters']['attributeToSearch'])
    elif httpMethod == getMethod and path == orderConfigPathAll:
        response = getOrderConfigAll(event['queryStringParameters']['customerId'])
    
    elif httpMethod == getMethod and path == botOutputPath:
        response = getBotResult(event['queryStringParameters']['display_id'])

    elif httpMethod == getMethod and path == botCounterPath:
        response = getBotCounterResult(event['queryStringParameters']['counter_id'])

    elif httpMethod == getMethod and path == marketDetails:
        response = getCoinMarketCap()
    
    else:
        response = buildResponse(400, {'message': 'Not Found'})
    
    return response

# API resource here. 
getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'

healthPath = '/health'
customerPath = '/customer'
customersPath = '/customers'
customerItemPath = '/customer/customerItem'

# customerApiSecret = '/customer/api-secret'
# customerRunning_status = '/customer/running_status'

orderConfigPath = '/orderConfiguration'
orderConfigPathAll = '/orderConfiguration/allData'

botOutputPath = '/botOutput'

botCounterPath = '/botCounter'

marketDetails = '/marketDetails'





# Check status code.
def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type' : 'application/json',
            'Access-Control-Allow-Origin' : '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response


    
def getCustomer(customerId):
    try:
        # customerId = int(customerId)
        response = customer_table.get_item(
            Key={
                'customerId': customerId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % customerId})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle


def getCustomerItem(customerId, attributeToSearch):
    try:
        customerId = str(customerId)
        response = customer_table.get_item(
            Key={'customerId': customerId}
        )
        if 'Item' in response:
            customer_item = response['Item']
            data = customer_item.get(attributeToSearch)

            if data is not None:
                return buildResponse(200, data)
            else:
                return buildResponse(404, {'Message': f'Attribute not found for customerId: {customerId}'})
        else:
            return buildResponse(404, {'Message': f'Item not found for customerId: {customerId}'})
    except Exception as e:
        logger.exception(f"{e}")
        return buildResponse(500, {'Message': 'Failed to retrieve item'})
    
    
def modifyCustomerInfo(customerId, updateKey, updateValue):
    try:
        response = customer_table.update_item(
            Key={
                'customerId' : customerId
            },
            UpdateExpression = 'set %s = :value' % updateKey,
            ExpressionAttributeValues={
                ':value': updateValue
            },
            ReturnValues="UPDATED_NEW"
        )
        body = {
            'Operation' : 'UPDATE',
            'Message' : 'SUCCESS',
            'UpdatedAttributes' : response
        }
        return buildResponse(200, body=body)
    except Exception as e:
        error_handle = logger.exception(f'{e}')
        return error_handle



def saveCustomer(requestBody):
    try:
        customer_table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body=body)
    except Exception as e:
        logger.exception(f"{e}")
        body = {
            'Operation': 'SAVE',
            'Message': 'FAILED',
            'Error': str(e)
        }
        return buildResponse(500, body=body)


def saveOrderConfig(requestBody):
    try:
        order_configuration_table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body=body)
    except Exception as e:
        logger.exception(f"{e}")
        body = {
            'Operation': 'SAVE',
            'Message': 'FAILED',
            'Error': str(e)
        }
        return buildResponse(500, body=body)



def getOrderConfigAll(customerId):
    try:
        # customerId = int(customerId)
        response = order_configuration_table.get_item(
            Key={
                'customerId': customerId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % customerId})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle


def getOrderConfig(customerId, attributeToSearch):
    try:
        customerId = str(customerId)
        response = order_configuration_table.get_item(
            Key={'customerId': customerId}
        )
        if 'Item' in response:
            order_config = response['Item']
            data = order_config.get(attributeToSearch)

            if data is not None:
                return buildResponse(200, data)
            else:
                return buildResponse(404, {'Message': f'Attribute not found for customerId: {customerId}'})
        else:
            return buildResponse(404, {'Message': f'Item not found for customerId: {customerId}'})
    except Exception as e:
        logger.exception(f"{e}")
        return buildResponse(500, {'Message': 'Failed to retrieve item'})
    

def getCustomerApiKey(customerId):
    try:
        # customerId = int(customerId)
        response = customer_table.get_item(
            Key={
                'customerId': customerId
            }
        )
        if 'Item' in response:
            customer_data = response['Item']
            api_key = customer_data.get('apiKey')
            
            if api_key is not None:
                return buildResponse(200, api_key)
            else:
                return buildResponse(400, {'Message': 'API key not found for customerId: %s' % customerId})
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % customerId})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle


def getCustomerApiSecret(customerId):
    try:
        # customerId = int(customerId)
        response = customer_table.get_item(
            Key={
                'customerId': customerId
            }
        )
        if 'Item' in response:
            customer_data = response['Item']
            api_secret = customer_data.get('apiSecret')
            
            if api_secret is not None:
                return buildResponse(200, api_secret)
            else:
                return buildResponse(400, {'Message': 'API key not found for customerId: %s' % customerId})
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % customerId})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle


def getCustomerRunningStatus(customerId):
    try:
        # customerId = int(customerId)
        response = customer_table.get_item(
            Key={
                'customerId': customerId
            }
        )
        if 'Item' in response:
            customer_data = response['Item']
            running_status = customer_data.get('running_status')
            
            if running_status is not None:
                return buildResponse(200, running_status)
            else:
                return buildResponse(400, {'Message': 'API key not found for customerId: %s' % customerId})
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % customerId})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle
    
    
def getBotResult(display_id):
    try:
        display_id = str(display_id)
        response = bot_output_table.get_item(
            Key={
                'display_id': display_id
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % display_id})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle
    
  

def getBotCounterResult(counter_id):
    try:
        counter_id = str(counter_id)
        response = table.get_item(
            Key={
                'counter_id': counter_id
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(400, {'Message': 'customerId: %s not found' % counter_id})
    except Exception as e:
        error_handle = logger.exception(f"{e}")
        return error_handle
    