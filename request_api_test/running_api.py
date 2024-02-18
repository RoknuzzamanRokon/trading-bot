import requests


url = 'https://zyv0q9hl1g.execute-api.us-east-2.amazonaws.com/config-stage/health'


while True:
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f'Status code: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')


