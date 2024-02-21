import requests

url = "https://zyv0q9hl1g.execute-api.us-east-2.amazonaws.com/config-stage/botCounter"
params = {'counter_id': '1'}

response = requests.get(url=url, params=params)
print(response.json())