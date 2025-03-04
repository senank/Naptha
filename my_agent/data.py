import requests

from typing import Dict
from logging import getLogger

logger = getLogger(__name__)
from .constants import ASHBY_API_KEY, ASHBY_API_URL

sync_token = None  # TODO: data: Determine if sync token lasts for all queries
next_cursor = None  # TODO: data: Determine if cursor lasts for all queries

# APPLICANT DATA
def get_all_job_applications(job_posting_id: str):
    """
    Parses all applications and formats a new list where all are new
    """
    applications = _fetch_all_job_applications(job_posting_id)
    # TODO: data: How to determine if already processed an application: "currentInterviewStage"?
    # new_applications = []
    # for application in applications:
    #     if application["stage"]["name"] == "New":
    #         new_applications.append(application)
    return applications


def _fetch_all_job_applications(job_posting_id: str):
    """
    Gets all job applications to a specific job
    """
    url = ASHBY_API_URL + "/applications.list"
    json = {
        "limit": 50,
        "jobId": job_posting_id
    }
    applications = _sync_job_id_application_ashby(url, json)

    logger.info(f"Found {len(applications)} from endpoint")
    if applications:
        logger.info(f"Applications look like this:\n\n{applications[0]}\n\n")
    return applications


def _sync_job_id_application_ashby(url: str, payload: Dict):
    data = []

    if sync_token:  # Checks if already synced
        # TODO: data: MUST BE CALLED ATLEAST 1 PER WEEK OR SYNC TOKEN EXPIRES
        payload['syncToken'] = sync_token
    
    if next_cursor:  # Checks where left off
        payload['nextCursor'] = next_cursor
    
    try:
        while True:  # Get all new applications (payload specifies job_id)
            response = requests.post(
                url,
                json=payload,
                headers = {
                    'Accept': 'application/json; version=1',
                    'Content-Type': 'application/json',
                },
                auth=(ASHBY_API_KEY, '')
            )
            if not response:
                logger.error("Failed respons in _send_request_to_ashby")
            
            data += response["results"]
            
            sync_token = response.get("syncToken", None)
            next_cursor = response.get("nextCursor", "")
            
            if sync_token:
                payload["syncToken"] = sync_token
            payload["nextCursor"] = next_cursor
            
            if response["moreDataAvailable"] == False:  # If there is more loop again
                break
        
        return data
    except Exception as e:
        logger.error(f"_send_request_to_ashby: {e}")


# JOB DATA
def get_job_posting_data(job_posting_id: str):
    url = ASHBY_API_URL + "/job.info"
    json = {
        "id": job_posting_id
    }
    job_data = _send_fetch_job_description(url, json)
    if not job_data:
        logger.info("No Job data found")
        return {}
    
    final_job_data = {}
    final_job_data["name"] = job_data["job"]["name"]
    final_job_data["info"] = job_data["openings"]["latestVersion"]["description"]

    return final_job_data


def _send_fetch_job_description(url: str, payload: Dict):
    """
    Gets the job information
    """
    return requests.post(
        url,
        json=payload,
        headers = {
            'Accept': 'application/json; version=1',
            'Content-Type': 'application/json',
        },
        auth=(ASHBY_API_KEY, '')
    )



