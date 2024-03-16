from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY_3')
api_secret = os.environ.get('API_SECRET_3')

client = Client(api_key, api_secret)

try:
    # Get the accounts for both USDC and ATOM
    usdc_account_id = 'f31a64bf-b49b-51ff-8ad6-2b12932fa63f'
    atom_account_id = '96a98d32-e744-5c7e-92e2-847c7da764e9'

    # Set the amount of USDC you want to transfer
    usdc_amount = '10.0'

    # Sell USDC for USD
    sell_order = client.sell(
        usdc_account_id,
        amount=usdc_amount,
        currency='USDC',  # Specify the currency as USDC
        commit=True  # Commit the sell immediately
    )

    # Check if the sell order was successful
    if sell_order['status'] == 'completed':
        print("USDC sell order successful!")
        
        # Get the USD amount from the sell order
        usd_amount = sell_order['subtotal']['amount']

        # Buy ATOM with the USD
        buy_order = client.buy(
            atom_account_id,
            amount=usd_amount,
            currency='ATOM',  # Specify the currency as ATOM
            commit=True  # Commit the buy immediately
        )

        # Check if the buy order was successful
        if buy_order['status'] == 'completed':
            print("ATOM buy order successful!")
        else:
            print("ATOM buy order failed:", buy_order['status'])
    else:
        print("USDC sell order failed:", sell_order['status'])

except Exception as e:
    print("Error:", e)

