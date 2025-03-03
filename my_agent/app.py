"""
app.py
======

Flask application for LangGraph-based agent workflows.

This file defines a Flask web application that serves as an interface for interacting 
with a LangGraph agent to perform automated workflows such as generating daily and monthly summaries. 
The application includes endpoints for health checks, invoking the daily/monthly summary process, 
and validating request data against a JSON schema.

Endpoints:
    - GET `/`: Basic health check endpoint to confirm the application is running.
    - POST `/daily_summary`: Validates incoming request data, invokes the LangGraph agent 
                             to process a daily summary workflow, and returns the result.
    - POST `/monthly_summary`: Validates incoming request data, invokes the LangGraph agent 
                               to process a daily summary workflow, and returns the result.
Functions:
    - home(): Basic health check function.
    - daily_summary(): Processes daily summary requests by validating input data, invoking
      the LangGraph agent, and returning the result.
    - _validate_generate_daily_report(data: Dict): Validates request data against a 
      predefined JSON schema for generating daily summaries.
    - _get_json_schema_daily_report_gen(): Provides the JSON schema required to validate
      daily summary generation requests.


Error Handling:
    - Ensures proper error handling and logging for JSON validation, agent invocation, 
      and unexpected runtime issues.

Dependencies:
    - Flask: Web framework for handling HTTP requests.
    - LangGraph: Framework for defining and invoking automated workflows.
    - jsonschema: For validating incoming JSON request data against a schema.

"""
from flask import Flask, request, jsonify


from .resume_analysis import get_resume_analysis_agent
from .constants import JSON_JOB_NAME, JSON_JOB_INFO

from .resume_analysis_utils.states.main_states import InputState
import logging

from typing import Dict

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
logging.info("Logging setup")

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "working!"

@app.route('/resume_analysis', methods=['POST'])
def resume_analysis():
    """
    Handles the `/resume_analysis` endpoint for processing daily summary requests.

    This function validates the incoming JSON request, initializes the LangGraph 
    daily summary workflow, and invokes the agent with the provided input data. 
    The workflow processes the input to generate a daily summary, and the result 
    is returned as a JSON response.

    Returns:
        Response: A Flask JSON response with the following:
            - HTTP 200: If the workflow completes successfully, returns the status 
              and the workflow result.
            - HTTP 400: If the request content is not valid JSON or fails validation.
            - HTTP 500: If an unexpected error occurs during workflow execution.

    Example:
        Request (POST /resume_analysis):
        {
            "JSON_CLIENT_NAME": "Client A",
            "JSON_ARTICLES_TO_INCLUDE": ["Article 1", "Article 2"]
        }

        Response (HTTP 200):
        {
            "status": "success",
            "result": {
                ...
            }
        }
    """
    data = []
    try:
        from .resume_analysis_utils.nodes.subgraph_nodes import check_contribution_count, check_user_exists
        test_github = check_user_exists("senank")
        tesT_count = check_contribution_count("senank")
        app.logger.info(f"This use exists: {test_github} with {tesT_count} contributions")
        # Initialize the workflow
        agent = get_resume_analysis_agent()
        result = agent.invoke(InputState(resumes=data))

        # Return the result as JSON
        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        app.logger.error(f"Error while running the agent: {str(e)}")
        return jsonify({"error": f"Failed to process the request: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
