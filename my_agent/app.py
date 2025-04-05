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
from .data import AshbyClient, ApplicationProcessor
from .constants import JOB_IDS, ASHBY_WEBHOOK_SECRET, TECH_JOBS

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

    if not data:
        app.logger.error("No data recieved in response")
        return jsonify({"error": "No data prorecievedvided in response"}), 400

    _validate_resume_analysis_schema(data)

    # TODO Validate secret -> webhook authentication
    # if not _validate_signature(request):
    #     return jsonify({"error": "Invalid signature from webhook"}), 400

    # Checks event type is application created
    if data['action'] != "applicationSubmit":
        return jsonify({"message": "Not a submitted application"}), 200
    
    # Checks the job is for the job wanted
    job_id = data['data']['application']['job']['id']
    if job_id not in JOB_IDS:
        return jsonify({"message": "Not a valid job ID"}), 200
    
    try:
        # Get all new applicants for this job_id
        client = AshbyClient()
        application_processor = ApplicationProcessor(client)
        job_data = client.get_job_data(job_id)
        job_name = job_data["name"]
        applicants = application_processor.get_applications(job_id, job_name)

        # send application to resume analysis agent
        if job_name in TECH_JOBS:
            agent = get_resume_analysis_agent(tech=True)
        else:
            agent = get_resume_analysis_agent(tech=False)

        result = agent.invoke(InputState(
            job_data=job_data,
            applicants=applicants
        ))

        if not result:
            return jsonify({"error": "agent failed"}), 500
        
        # update ashby fields with results
        classifications = result['final_classification']
        client.update_application_score(classifications)
        return jsonify({"message": f"Successfully updated {len(classifications)} candidates"}), 200 

    except ValidationError as e:
        return jsonify({"error": f"incorrect data input: {str(e)}"}), 500
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
        "additionalProperties": True
    }


def _validate_signature(request):
    try:
        app.logger.info(f"this is the json {request.get_json()}")
        # app.logger.info(f"{request.json()}")
        secret = request.get_json()["results"]['secretToken']

        # ? TODO: Add secret and encryption
        return ASHBY_WEBHOOK_SECRET == secret
    except Exception as e:
        app.logger.info(f"Failed to validate secret {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
