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

4) ```python3 -m pytest -s -v``` to test with sample endpoint



For next steps:
- Setting up a CICD workflow/functions that check if field exists, if not create else track customField ID for Applications in Ashby
- Optimize agent
  - Prompt engineering/refinement of process
  - Quality checks
  - Add tech/non-tech analysis capabilities
- Add agent to naptha hub
  - Integrate so code runs on naptha hub
  - This app will then handle the webhook and invoke the agent via the naptha sdk rather than directly from source code
- Test sync tokens for Ashby API calls
- App security + hosting
  - Requires a server
  - CORS and/or firewall on host
  - Schema validation
  - Update secrets header for Ashby
  - Error handling
- Logging, docstrings and documentation