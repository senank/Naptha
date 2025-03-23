"""
constants.py
=============

This module defines agent-specific constants used for configuration, JSON request/response processing, 
database schema mapping, and embedding-related settings.

The constants are categorized into the following sections:
1. General Limits: Defines agent-specific thresholds such as maximum number of articles to include in daily output.
2. Database Fields: Maps database column names to their corresponding internal keys or environment variables.
3. JSON Keys: Maps JSON request/response fields to their corresponding internal keys.
4. Embedding Settings: Defines constants related to embedding input size, chunking, and processing.
"""
import os

JOB_IDS = ["82646b74-6c72-41a2-85a2-c8988a71fd53"]
TECH_JOBS = ["Software Engineer (Intern)"]
NON_TECH_JOBS = []

# Ashby API
ASHBY_API_KEY = os.getenv("ASHBY_API_KEY", "")
ASHBY_WEBHOOK_SECRET = os.getenv("ASHBY_WEBHOOK_SECRET", "")
ASHBY_API_URL = "https://api.ashbyhq.com"
ASHBY_SCORE_FIELD_ID = "3fbc8a21-18a1-4a61-b435-e76b80ff3eea"

if not ASHBY_API_KEY:
    raise ValueError("ASHBY_API_KEY must be set in the environment variables.")

if not ASHBY_WEBHOOK_SECRET:
    raise ValueError("ASHBY_WEBHOOK_SECRET must be set in the environment variables.")

