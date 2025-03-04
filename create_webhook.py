import requests
from my_agent.constants import ASHBY_API_KEY

url = "https://api.ashbyhq.com/webhook.create"

payload = {
    "webhookType": "applicationSubmit",
    "requestUrl": "https://bb6b-142-59-161-199.ngrok-free.app/resume_analysis",
    "secretToken": "secret"
}
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, auth=(ASHBY_API_KEY, ''))

print(response.text)