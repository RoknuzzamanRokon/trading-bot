import requests

url = "https://zyv0q9hl1g.execute-api.us-east-2.amazonaws.com/config-stage/botOutput"
params = {'display_id': '1'}

response = requests.get(url=url, params=params)
print(response.json())