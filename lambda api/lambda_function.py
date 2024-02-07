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
from coinbase_advanced_trader.strategies.fear_and_greed_strategies import trade_based_on_fgi_simple, fiat_limit_sell
from boto3.dynamodb.conditions import Attr,Key


logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Database Connection.
dynamodb = boto3.resource('dynamodb')
table_1 = 'artmix_tb4_table_01'
table = dynamodb.Table(table_1)

table_2 = 'customer-table'
customer_table = dynamodb.Table(table_2)

table_3 = 'order-configuration-table'
order_configuration_table = dynamodb.Table(table_3)

table_4 = 'bot-output-table'
bot_output_table = dynamodb.Table(table_4)

# Environment variable section.
load_dotenv()
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')
set_api_credentials(API_KEY, API_SECRET)


USD_Size = 10
symbol = 'ETH'
product_id = f"{symbol}-USD"


max_buy = 10
max_sell = 10

PROFIT_PERCENTAGE = 0.71
LOSS_PERCENTAGE = 0.70


update_time = 5
btc_size = int(USD_Size)
running = True
sell_counter = 0
buy_counter = 0
window_size = 8
window_size_for_rsi = 14 
sell_btc_size = btc_size + 0.06

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
    

def update_buy_sell_counter(buy_count,sell_count,total_buy,total_sell,current_price):
    data_to_insert = {
            'counter_id': 1, 
            'buy_counter': int(buy_count),
            'sell_counter': int(sell_count),
            'total_buy': int(total_buy),
            'total_sell': int(total_sell),
            'current_price': Decimal(current_price)
        }
        
    try:
        # Insert or update data into DynamoDB
        response = table.put_item(Item=data_to_insert)
        return response
    except Exception as e:
        print(f"Error updating buy counter: {e}")
        return None

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
        print(f"Error retrieving buy counter: {e}")
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
        print(f"Error retrieving total buy counter: {e}")
        return 0
    
def get_total_sell():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('total_sell')
    except Exception as e:
        print(f"Error retrieving total sell counter: {e}")
        return 0
        
def get_current_price():
    try:
        response = table.get_item(Key={'counter_id': 1})
        item = response.get('Item', {})
        return item.get('current_price')
    except Exception as e:
        print(f"Error retrieving current price: {e}")
        return 0
    

def lambda_handler(event, context):
    global buy_counter, sell_counter, running, max_buy, max_sell, update_time, buy_counter_db, window_size_for_rsi, btc_size, sell_btc_size
    
    buy_check = get_buy_counter()
    sell_check = get_sell_counter()
    
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']
    
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
    
    get_current_price_db = get_current_price()
    
    historical_prices = get_last_month_prices(symbol)
    moving_average = calculate_moving_average(historical_prices, window_size)
    print(f'Moving Average: {moving_average}')

    closing_price_result = get_last_day_closing_price(coin_symbol=symbol)
    print(f"Closing price: {closing_price_result} \n")
    
    update_price_result = get_coinbase_price(coin_symbol=symbol)
    print(f"Current Price: {update_price_result} \n")
        
    trade_buy_amount = loss_amount(closing_price_result, LOSS_PERCENTAGE)
    print(f"Buy Amount Price: {trade_buy_amount}")
    
    
    if buy_check == 0:
        trade_sell_amount = profit_amount(closing_price_result, PROFIT_PERCENTAGE)
        print(f"Sell Amount Price: {trade_sell_amount} \n")
        
    else:
        trade_sell_amount = profit_amount(get_current_price_db, PROFIT_PERCENTAGE)
        print(f"Sell Amount Price: {trade_sell_amount} \n")
          
    closing_prices = get_last_60_closing_prices(coin_symbol=symbol)

    if not isinstance(closing_prices, str):
        
        rsi = calculate_rsi(closing_prices, window_size_for_rsi)
        print(f'The RSI for the result candle prices per minute is: {rsi}')
    
    
    if update_price_result is not None:
        update_price_float = float(update_price_result)
        if buy_counter < max_buy and total_buy < max_buy and rsi <= 30 and buy_check == 0:
            
            # trade_based_on_fgi_simple(product_id, btc_size)

            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Buy~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~') 
            buy_counter += 1

            total_buy += 1
            total_sell += 0
            
            current_price = get_coinbase_price(coin_symbol=symbol)
            print(type(current_price))

            set_buy = 1
            set_sell = 0
            update_buy_sell_counter(set_buy, set_sell, total_buy, total_sell, current_price)
           

        elif sell_counter < max_sell and  total_sell < max_sell and buy_check > 0 and trade_sell_amount <= update_price_float:
            
            # fiat_limit_sell(product_id, sell_btc_size)
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Sell~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            sell_counter += 1

            total_buy += 0
            total_sell += 1

            reset_buy = 0
            reset_sell = 0
            reset_current_price = 0
            update_buy_sell_counter(reset_buy, reset_sell, total_buy, total_sell, reset_current_price)

        elif sell_counter == max_sell and buy_counter == max_buy:
            running = False
    else:
        print('Skipping due to an error in obtaining the current price.')




    # This is API section.
    
    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == postMethod and path == customerPath:
        response = saveCustomer(json.loads(event['body']))
    elif httpMethod == getMethod and path == customerPath:
        response = getCustomer(event['queryStringParameters']['customerId'])
    elif httpMethod == getMethod and path == customerApiKey:
        response = getCustomerApiKey(event['queryStringParameters']['customerId'])
    elif httpMethod == getMethod and path == customerApiSecret:
        response = getCustomerApiSecret(event['queryStringParameters']['customerId'])
    elif httpMethod == patchMethod and path == customerPath:
        requestBody = json.loads(event['body'])
        response = modifyCustomerInfo(requestBody['customerId'], requestBody['updateKey'], requestBody['updateValue'])

    elif httpMethod == postMethod and path == orderConfigPath:
        response = saveOrderConfig(json.loads(event['body']))
    elif httpMethod == getMethod and path == orderConfigPath:
        response = getOrderConfig(event['queryStringParameters']['customerId'], event['queryStringParameters']['attributeToSearch'])


    else:
        response = buildResponse(400, {'message': 'Not Found'})
    
    time.sleep(update_time)
    
    return response

# API resource here. 
getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'

healthPath = '/health'
customerPath = '/customer'
customersPath = '/customers'
customerApiKey = '/customer/api-key'
customerApiSecret = '/customer/api-secret'

orderConfigPath = '/orderConfiguration'


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
    

def getCustomer(customerId):
    try:
        customerId = int(customerId)
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


def getCustomerApiKey(customerId):
    try:
        customerId = int(customerId)
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
        customerId = int(customerId)
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


def saveOrderConfig(requestBody):
    try:
        # Convert numeric values to Decimal 
        requestBody["customerId"] = int(requestBody["customerId"])
        requestBody["symbol"] = str(requestBody["symbol"])
        requestBody["product_id"] = str(requestBody["product_id"])
        requestBody["usd_size"] = Decimal(str(requestBody["usd_size"]))
        requestBody["max_buy"] = Decimal(str(requestBody["max_buy"]))
        requestBody["max_sell"] = Decimal(str(requestBody["max_sell"]))
        requestBody["PROFIT_PERCENTAGE"] = Decimal(str(requestBody["PROFIT_PERCENTAGE"]))
        requestBody["LOSS_PERCENTAGE"] = Decimal(str(requestBody["LOSS_PERCENTAGE"]))

        # Put the item into DynamoDB
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
    

def getOrderConfig(customerId, attribute_to_search):
    try:
        customerId = int(customerId)
        response = order_configuration_table.get_item(
            Key={'customerId': customerId}
        )
        if 'Item' in response:
            order_config = response['Item']
            data = order_config.get(attribute_to_search)

            if data is not None:
                return buildResponse(200, data)
            else:
                return buildResponse(404, {'Message': f'Attribute not found for customerId: {customerId}'})
        else:
            return buildResponse(404, {'Message': f'Item not found for customerId: {customerId}'})
    except Exception as e:
        logger.exception(f"{e}")
        return buildResponse(500, {'Message': 'Failed to retrieve item'})