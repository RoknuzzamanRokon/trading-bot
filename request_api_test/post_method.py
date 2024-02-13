import requests

url = "https://zyv0q9hl1g.execute-api.us-east-2.amazonaws.com/config-stage/customer"

headers = {
    "Content-Type" : "application/json",
}


data = {
    "apiSecret":"dfsaadf",
    "userName":"rooookkkooon",
    "emailId": "asdsa@gmail.com",
    "apiKey": "asdas22222222",
    "customerId": "gagag34qrf43",
    "password": "12121212"

}


response = requests.post(url, json=data, headers=headers)

print(response.status_code)
print(response.json())