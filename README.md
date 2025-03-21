1) Set up env with 
```
OPENAI_API_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=
ASHBY_API_KEY=
```

2) ```docker-compose -f docker-compose.prod.yml up --build```
    - application lives on 8000 port
    - use ```ngrok http 80``` for nginx and expose nginx app for webhook

3) Setup Ashby
    - update url (and secret for prod) then run```python create_webhook.py```
    - Add customfield (if not exists) to Ashby
    - TODO: Setting up a CICD workflow/functions that check if field exists, if not create else track customField ID for Applications in Ashby

4) ```python3 -m pytest -s -v``` to test with sample endpoint