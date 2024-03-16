from coinbase.wallet.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY_2')
api_secret = os.environ.get('API_SECRET_2')

client = Client(api_key, api_secret)

try:
    user = client.get_current_user()
    print("API key is valid.")
    # print(user)

    # Get source and destination account IDs
    source_account_id = 'f31a64bf-b49b-51ff-8ad6-2b12932fa63f'  # Replace with the actual source account ID
    destination_account_id = '96a98d32-e744-5c7e-92e2-847c7da764e9'  # Replace with the actual destination account ID

    # Set the amount and currency for the transfer
    amount = '1.0'  # Replace with the desired amount
    currency = 'USDC'  # Replace with the desired currency

    # Perform the balance transfer
    transfer_response = client.transfer_money(
        source_account_id,
        to=destination_account_id,
        amount=amount,
        currency=currency,
        description='Balance Transfer'
    )

    # Print transfer details
    print("Transfer successful!")
    print("Transfer ID:", transfer_response['data']['id'])
    print("Transfer Amount:", transfer_response['data']['amount']['amount'], transfer_response['data']['amount']['currency'])
    print("Transfer Status:", transfer_response['data']['status'])

except Exception as e:
    print("API key is invalid or transfer failed. Error:", e)

