import requests

url = "https://zyv0q9hl1g.execute-api.us-east-2.amazonaws.com/config-stage/orderConfiguration"

headers = {
    "Content-Type" : "application/json",
}


data = {
    "customerId": "3",
    "symbol": "ETH",
    "usd_size": 10,
    "product_id": "ETH-USD",
    "max_buy" : 10,
    "max_sell" : 10,
    "PROFIT_PERCENTAGE" : "0.74",
    "LOSS_PERCENTAGE" : "0.75"
}

response = requests.post(url, json=data, headers=headers)

print(response.status_code)
print(response.json())