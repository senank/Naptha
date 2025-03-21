import requests

from typing import Dict, List
from logging import getLogger
from time import time

from io import BytesIO
from PyPDF2 import PdfReader

logger = getLogger(__name__)
from .constants import ASHBY_API_KEY, ASHBY_API_URL, ASHBY_CUSTOM_FIELD

sync_token = None  # ? TODO: data: Determine if sync token lasts for all queries
next_cursor = None  # ? TODO: data: Determine if cursor lasts for all queries
last_updated = None

# Ashby Pull Sync
def _valid_time_difference(prev):
    difference = (time() - prev) * 60 * 60 * 24  # days
    if difference > 6:
        return False
    return True


def _get_sync_token():
    if not last_updated:
        return None, None
    if not _valid_time_difference(last_updated):
        return None, None
    return sync_token, next_cursor


# APPLICANT DATA
def get_all_job_applications(job_posting_id: str) -> List[Dict]:
    """
    Parses all applications and formats a new list where all are new
    """
    logger.info(f"getting job applications for {job_posting_id}")
    applications = _fetch_all_job_applications(job_posting_id)
    relevant_applications = _get_relevant_application_data(applications)
    return relevant_applications


def get_batch_job_applications(job_posting_id: str) -> List[Dict]:
    """
    Parses all applications and formats a new list where all are new
    """
    logger.info(f"getting job applications for {job_posting_id}")
    applications = _fetch_batch_job_applications(job_posting_id)
    relevant_applications = _get_relevant_application_data(applications)
    return relevant_applications


def _get_applicant_info(id_):
    url = ASHBY_API_URL + "/candidate.info"
    json = {
        "id": id_,
    }
    app_info = {'cand_id': id_}
    response_data = _send_request_to_ashby(url, json)
    app_info["name"] = response_data["name"]
    app_info["github"] = ""
    
    # get github username
    for link in response_data["socialLinks"]:
        if link["type"] == "GitHub":
            app_info["github"] = link["url"].rstrip("/").split("/")[-1]
            break
        
    if not app_info["github"]:  # only here to prevent unneccessary calls to Ashby api
        app_info["resume"] = ""
        return app_info
    
    # Get resume link
    app_info["resume"] = _get_resume_data(response_data["resumeFileHandle"]["handle"])
    return app_info


def _get_relevant_application_data(applications: List[Dict]) -> List[Dict]:
    """
    Parses applications to get only viable applications
    """
    processed_applications = []
    for application in applications:
        if application['status'] != "Active" or application["currentInterviewStage"]["type"] != "PreInterviewScreen":  #? what is needed to not consider application
            continue
        cand_id = application['candidate']['id']
        applicant = _get_applicant_info(cand_id)
        applicant['app_id'] = application['id']
        # if applicant.get("github", ""):
        processed_applications.append(applicant)
    return processed_applications


def _get_resume_data(handle):
    response = requests.post(
        ASHBY_API_URL + "/file.info",
        json={"fileHandle": handle},
        headers = {
            'Accept': 'application/json; version=1',
            'Content-Type': 'application/json',
        },
        auth=(ASHBY_API_KEY, '')
    )
    url = response.json()["results"]["url"]
    response = requests.get(url)
    response.raise_for_status()
    pdf_file = BytesIO(response.content)
    reader = PdfReader(pdf_file)

    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)


def _fetch_all_job_applications(job_posting_id: str):
    """
    Gets all job applications to a specific job
    """
    url = ASHBY_API_URL + "/application.list"
    json = {
        "limit": 50,
        "jobId": job_posting_id
    }
    # applications = _sync_job_id_application_ashby(url, json)
    applications = _sync_job_id_application_ashby(url, json)

    logger.info(f"Found {len(applications)} from endpoint")
    if applications:
        logger.info(f"Applications look like this:\n\n{applications[0]}\n\n")
    return applications

def _fetch_batch_job_applications(job_posting_id: str):
    """
    Gets all job applications to a specific job
    """
    url = ASHBY_API_URL + "/application.list"
    json = {
        "limit": 5,
        "jobId": job_posting_id
    }
    applications = _send_request_to_ashby(url, json)

    logger.info(f"Found {len(applications)} from endpoint")
    if applications:
        logger.info(f"Applications look like this:\n\n{applications[0]}\n\n")
    return applications


def _sync_job_id_application_ashby(url: str, payload: Dict):
    data = []
    sync_token, next_cursor = _get_sync_token()
    if sync_token:  # Checks if already synced
        # ?: data: MUST BE CALLED ATLEAST ONCE PER 6 DAYS OR SYNC TOKEN EXPIRES
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
            
            data += response.json()['results']
            
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


def _send_request_to_ashby(url: str, payload: str):
    response = requests.post(
        url,
        json=payload,
        headers = {
            'Accept': 'application/json; version=1',
            'Content-Type': 'application/json',
        },
        auth=(ASHBY_API_KEY, '')
    )
    return response.json()["results"]

# JOB DATA
def get_job_posting_data(job_id: str):
    # Get Job Posting ID
    logger.info("getting job posting from id")
    url = ASHBY_API_URL + "/job.info"
    json = {
        "id": job_id
    }
    job_data = _send_fetch_job_description(url, json)
    if not job_data:
        logger.info("No Job data found")
        return {}
    job_posting_id = job_data["jobPostingIds"][0]
    
    # Get job info from posting
    logger.info("getting job info from posting")
    url = ASHBY_API_URL + "/jobPosting.info"
    json = {
        "jobPostingId": job_posting_id
    }
    job_posting_data = _send_fetch_job_description(url, json)
    if not job_posting_data:
        logger.info("No Job data found")
        return {}
    
    final_job_data = {}
    final_job_data["job_id"] = job_id
    final_job_data["name"] = job_posting_data["title"]
    final_job_data["info"] = job_posting_data["descriptionPlain"]

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
    ).json()["results"]


# UPDATE ASHBY
def update_fields_in_ashby(candidates):
    for application_id, score in candidates:
        logger.info(f"{application_id} {score}")
        # update customfield for ashby
        update_response = _update_field(application_id, float(score))
        logger.info(f"{update_response}")
    logger.info(f"Successfully updated all fields")
    

def _update_field(candidate_id, score):
    url = ASHBY_API_URL + "/customField.setValue"
    payload = {
        "objectType": "Application",
        "fieldValue": score,
        "fieldId": ASHBY_CUSTOM_FIELD,
        "objectId": candidate_id
    }
    return _send_request_to_ashby(url, payload)

