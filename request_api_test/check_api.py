import requests

api_key = 'EWh5SIcfD8rX8vb6'
api_secret = 'TLgCQKh0HrAVxsCkyuLBgL7QLj1kR15U'

url = 'https://api.coinbase.com/v2/user'

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}',
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Check if the response contains the expected data or status
    if 'data' in response.json() and 'id' in response.json()['data']:
        print('API key is valid!')
    else:
        print(f'API key is not valid. Response: {response.json()}')

except requests.exceptions.HTTPError as err:
    print(f'HTTP error occurred: {err}. Response: {response.json()}')
except Exception as e:
    print(f'An error occurred: {e}')
