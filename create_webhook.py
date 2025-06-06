import requests
from my_agent.constants import ASHBY_API_KEY

url = "https://api.ashbyhq.com/webhook.create"

payload = {
    "webhookType": "applicationSubmit",
    "requestUrl": "https://3bef-142-59-161-199.ngrok-free.app/test_ashby_webhook",
    "secretToken": "secret"
}
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, auth=(ASHBY_API_KEY, ''))

print(response.text)