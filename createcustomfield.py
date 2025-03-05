import requests
from my_agent.constants import ASHBY_API_KEY

url = "https://api.ashbyhq.com/customField.create"

payload = {
    "fieldType": "Number",
    "objectType": "Application",
    "isExposableToCandidate": False,
    "title": "score",
    "description": "This field is the viability score at first glance for an application to a given job"
}
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, auth=(ASHBY_API_KEY, ''))

print(response.text)