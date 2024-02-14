from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import requests

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

parameters = {
  'start':'1',
  'limit':'10',
  'convert':'USD'
}
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': '2ce8972a-2751-4b3d-ab17-2e2cfd8a1a04'
}

# session = Session()
# session.headers.update(headers)

try:
  response = requests.get(url, params=parameters, headers)
  data = json.loads(response.text)
  print(data)
except (ConnectionError, Timeout, TooManyRedirects) as e:
  print(e)