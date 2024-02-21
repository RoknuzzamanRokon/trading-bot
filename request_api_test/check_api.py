from coinbase_advanced_trader.config import set_api_credentials

api_key = 'EWh5SIcfD8rX8vb6'
api_secret = 'TLgCQKh0HrAVxsCkyuLBgL7QLj1kR15U'


# Set the API credentials once, and it updates the CBAuth singleton instance
set_api_credentials(api_key, api_secret)

print(set_api_credentials.json())