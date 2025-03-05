import requests
from my_agent.constants import ASHBY_API_KEY

url = "https://api.ashbyhq.com/webhook.delete"

payload = { "webhookId": "44f7611e-5740-4421-aa79-5dfde01f46eb" }
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, auth=(ASHBY_API_KEY, ''))

print(response.text)