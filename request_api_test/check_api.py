from coinbase.wallet.client import Client

# Replace 'YOUR_API_KEY' and 'YOUR_API_SECRET' with your actual API key and secret
api_key = 'EWh5SIcfD8rX8vb6'
api_secret = 'TLgCQKh0HrAVxsCkyuLBgL7QLj1kR15U'

client = Client(api_key, api_secret)

try:
    user = client.get_current_user()
    print("API key is valid.")
    print(user['country'])
except Exception as e:
    print("API key is invalid. Error:", e)  