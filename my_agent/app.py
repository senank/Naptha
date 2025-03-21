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
from flask import Flask, request, jsonify, Request
from jsonschema import validate, ValidationError


from .resume_analysis import get_resume_analysis_agent
from .data import get_all_job_applications, get_job_posting_data, update_fields_in_ashby, get_batch_job_applications
from .constants import JOB_IDS, ASHBY_WEBHOOK_SECRET

from .resume_analysis_utils.states.main_states import InputState
import logging

from typing import Dict

import hmac
import hashlib

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
    This function gets triggered on webhooks from ashby on application creations.

    It does the following:
        - Pulls all the unsynced resumes that are not reviewed
        - Passes resumes to the agent
        - Updates Ashby CustomField to reflect the score
    """
    # Check response is json
    if not request.is_json:
        app.logger.error("Request content is not JSON.")
        return jsonify({"error": "Request content is not JSON"}), 400
    
    app.logger.debug("Received JSON data")
    data = request.get_json()

    # Checks event type is application created
    if data['action'] != "applicationSubmit":
        return jsonify({"message": "Not a submitted application"}), 200
    
    # Checks the job is for the job wanted
    if data['data']['application']['job']['id'] not in JOB_IDS:
        return jsonify({"message": "Not a valid job ID"}), 200
    
    try:
        # Get all new applicants for this job_id
        job_id = data['data']['application']['job']['id']
        job_data = get_job_posting_data(job_id)
        applicants = get_all_job_applications(job_id)

        # send application to resume analysis agent
        agent = get_resume_analysis_agent()
        result = agent.invoke(InputState(
            job_data=job_data,
            applicants=applicants
        ))

        if not result:
            return jsonify({"error": "agent failed"}), 500
        
        # update ashby fields with results
        classifications = result['final_classification']
        update_fields_in_ashby(classifications)
        return jsonify({"message": f"Successfully updated {len(classifications)} candidates"}), 200 


    except Exception as e:
        app.logger.error(f"Error while running the agent: {str(e)}")
        return jsonify({"error": f"Failed to process the request: {str(e)}"}), 500


# Validation
def _validate_resume_analysis_schema(data: Dict):
    try:
        data = request.get_json()
        validate(instance=data, schema=_get_json_schema_resume_analysis())
    except ValidationError as e:
        raise ValidationError(f"Invalid JSON format: {e.message}")


def _get_json_schema_resume_analysis():
    return {
        "type": "object",
        "properties":{
            "action": {"type": "string"},
            "data": {"type": "object"},

        },
        "required": ["action", "data"],
        "additionalProperties": False
    }


def _validate_signature(request):
    try:
        app.logger.info(f"this is the json {request.get_json()}")
        # app.logger.info(f"{request.json()}")
        secret = request.get_json()["results"]['secretToken']
        if not ASHBY_WEBHOOK_SECRET:
            app.logger.error("ASHBY_WEBHOOK_SECRET not set")
            return False
        
        if not secret:
            app.logger.error("No signature provided.")
            return False

        # ? TODO: Add secret and encryption
        return ASHBY_WEBHOOK_SECRET == secret
    except Exception as e:
        app.logger.info(f"Failed to validate secret {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
