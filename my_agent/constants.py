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
# JSON Keys
JSON_DAILY_OUTPUT_FORMAT = 'daily_output_style'
JSON_JOB_INFO = 'client_info'
JSON_JOB_NAME = 'client_name'