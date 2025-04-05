import requests

from typing import Dict, List
from logging import getLogger
from time import time

from io import BytesIO
from PyPDF2 import PdfReader

logger = getLogger(__name__)
from .constants import ASHBY_API_KEY, ASHBY_API_URL, ASHBY_SCORE_FIELD_ID, TECH_JOBS

class SyncToken:
    def __init__(self):
        self.sync_token = None  # ? TODO: data: Determine if sync token lasts for all queries
        self.last_updated = None

    def get_sync_token_and_cursor(self):
        if not self.last_updated:
            return None
        if not self.valid_time_difference():
            return None
        return self.sync_token
    
    def set_sync_token(self, token):
        logger.debug(f"Setting sync token")
        self.sync_token = token
        self.last_updated = time()

    def _valid_time_difference(self):
        difference_in_secs = (time() - self.last_updated) 
        difference_in_days = difference_in_secs / (60 * 60 * 24)
        return difference_in_days <= 6


class SyncTokenManager:
    sync_tokens = {}

    @classmethod
    def get_sync_token(cls, job_id) -> SyncToken:
        sync_token = cls.sync_tokens.get(job_id, None)
        if not sync_token:
            sync_token = SyncToken()
            cls.sync_tokens[job_id] = sync_token
        return sync_token


class AshbyClient:
    """
    Client to interact with Ashby API
    """
    def __init__(self, api_key=ASHBY_API_KEY, api_url=ASHBY_API_URL):
        self.api_key = api_key
        self.api_url = api_url
    
    def get_job_applications(self, job_posting_id: str):
        """
        Gets all job applications to a specific job
        """
        
        # applications = _sync_job_id_application_ashby(url, json)
        applications = self._fetch_job_applications(job_posting_id)

        logger.info(f"Found {len(applications)} from endpoint")
        if applications:
            logger.info(f"Applications look like this:\n\n{applications[0]}\n\n")
        return applications
    
    def get_applicant_info(self, id_):
        """
        Gets all candidate information
        """
        url = self.api_url + "/candidate.info"
        json = {
            "id": id_,
        }
        return self._send_request_to_ashby(url, json)
    
    def get_resume_data(self, handle):
        response = requests.post(
            self.api_url + "/file.info",
            json={"fileHandle": handle},
            headers = {
                'Accept': 'application/json; version=1',
                'Content-Type': 'application/json',
            },
            auth=(self.api_key, '')
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
    
    def get_job_data(self, job_id: str):
        # 1) Get Job Posting ID
        logger.info("getting job posting from id")
        job_posting_id = self._fetch_job_posting_id(job_id)
        if not job_posting_id:
            logger.info("No Job posting found")
            return {}
        
        # 2) Get job info from posting
        logger.info("getting job info from posting number")
        job_data = self._fetch_job_data(job_posting_id)
        if not job_data:
            logger.info("No Job data found")
            return {}
        
        # Extract relevant job data
        final_job_data = {}
        final_job_data["job_id"] = job_id
        final_job_data["name"] = job_data["title"]
        final_job_data["info"] = job_data["descriptionPlain"]

        return final_job_data

    def update_application_score(self, candidates):
        for application_id, score in candidates:
            logger.info(f"{application_id} {score}")
            # update customfield for ashby
            update_response = self._update_score_field(application_id, float(score))
            logger.info(f"{update_response}")
        logger.info(f"Successfully updated all fields")

    def _send_request_to_ashby(self, url: str, payload: Dict):
        return requests.post(
            url,
            json=payload,
            headers = {
                'Accept': 'application/json; version=1',
                'Content-Type': 'application/json',
            },
            auth=(ASHBY_API_KEY, '')
        ).json()["results"]

    def _fetch_job_applications(self, job_posting_id: str):
        """
        Gets all new job applications based on job_posting_id and last request.
        
        Uses sync token to track the state of all requested, and next cursor to
        track where the last request left off.
        """
        url = self.api_url + "/application.list"
        payload = {
            "jobId": job_posting_id,
            "status": "Active"
        }

        data = []
        sync_token_instance = SyncTokenManager.get_sync_token(job_posting_id)
        logger.info(f"Sync Token: {sync_token_instance.sync_token}")
        sync_token = sync_token_instance.get_sync_token_and_cursor()
        if sync_token:  # Checks if already synced
            # ?: data: MUST BE CALLED ATLEAST ONCE PER 6 DAYS OR SYNC TOKEN EXPIRES
            logger.debug(f"Sync token exists")
            payload['syncToken'] = sync_token
        
        try:
            count = 0
            while True:  # Get all new applications (payload specifies job_id)
                # ?: data: make this async; consider the payload data aswell
                logger.debug(f"Run {count}")
                response = requests.post(
                    url,
                    json=payload,
                    headers = {
                        'Accept': 'application/json; version=1',
                        'Content-Type': 'application/json',
                    },
                    auth=(self.api_key, '')
                )
                if not response:
                    logger.debug("Failed response in _send_request_to_ashby")
                    count += 1
                    if count > 5:
                        logger.error("Too many failed requests")
                        raise Exception("Too many failed requests")
                    continue
                
                response_data = response.json()

                # Handle expired sync token
                if (response_data["success"] == False) and (response_data["error"] == ["sync_token_expired"]):
                    logger.debug(f"Sync token has expired, resetting sync token")
                    sync_token_instance.set_sync_token(None)
                    del payload["syncToken"]
                    continue

                data += response_data['results']

                sync_token = response_data.get("syncToken", None)
                next_cursor = response_data.get("nextCursor", "")
                
                if sync_token and (response_data["moreDataAvailable"] == False):
                    logger.info(f"All data received")
                    logger.debug(f"Sync token: {sync_token}")
                    sync_token_instance.set_sync_token(sync_token)
                    break
                payload["cursor"] = next_cursor
                count += 1
                
            logger.debug(f"Total applications: {len(data)}")
            return data
        except Exception as e:
            logger.error(f"_fetch_job_applications: {e}")

    def _fetch_job_posting_id(self, job_id: str):
        """ Get Job Posting ID """
        url = self.api_url + "/job.info"
        json = {
            "id": job_id
        }
        job_data = self._send_request_to_ashby(url, json)
        if job_data:
            return job_data["jobPostingIds"][0]
        return ""
        
    def _fetch_job_data(self, job_posting_id: str):
        """ Get job info from posting id """
        url = self.api_url + "/jobPosting.info"
        json = {
            "jobPostingId": job_posting_id
        }
        job_data = self._send_request_to_ashby(url, json)
        if not job_data:
            return {}

        return job_data
        
    def _update_score_field(self, candidate_id, score):
        url = self.api_url + "/customField.setValue"
        payload = {
            "objectType": "Application",
            "fieldValue": score,
            "fieldId": ASHBY_SCORE_FIELD_ID,
            "objectId": candidate_id
        }
        return self._send_request_to_ashby(url, payload)

class ApplicationProcessor:
    """
    Gets and processes applications from Ashby API
    """
    def __init__(self, client: AshbyClient):
        self.applications = []
        self.client = client
    
    def get_applications(self, job_posting_id: str, job_name: str):
        logger.info(f"getting job applications for {job_posting_id}")
        self._get_new_applications(job_posting_id, job_name)
        return self.applications
    
    def _get_new_applications(self, job_posting_id: str, job_name: str) -> None:
        """
        Parses applications to get only viable applications
        """
        applications = self.client.get_job_applications(job_posting_id)
        logger.debug("Got applications")
        for application in applications:
            self._process_application(application, job_name)
    
    def _process_application(self, application, job_name) -> None:
        logger.debug(f"Processing application {application['id'], {job_name}}")
        if application["currentInterviewStage"]["type"] != "PreInterviewScreen":  #? what is needed to not consider application
            return

        cand_id = application['candidate']['id']
        app_id = application['id']
        logger.debug("Getting applicant info")
        applicant = self.client.get_applicant_info(cand_id)
        logger.debug("Got applicant info")
        logger.debug(f"Applicant is a tech job: {job_name in TECH_JOBS}")
        if job_name in TECH_JOBS:
            self._process_tech_applicant(applicant, cand_id, app_id)
        else:
            self._process_non_tech_application(applicant, cand_id, app_id)
        return
        
    def _process_tech_applicant(self, applicant, candidate_id, application_id) -> None:
        logger.debug("Processing tech application")
        parsed_applicant = {}
        parsed_applicant['cand_id'] = candidate_id
        parsed_applicant['app_id'] = application_id
        parsed_applicant["name"] = applicant["name"]
        parsed_applicant["github"] = ""
        logger.debug("parsed application stage 1")
        
        # get github username
        for link in applicant["socialLinks"]:
            if link["type"] == "GitHub":
                parsed_applicant["github"] = link["url"].rstrip("/").split("/")[-1]
                logger.debug("found github username")
                break
        logger.debug("parsed github username")
        if not parsed_applicant["github"]:  # prevents unneccessary calls to get resume from Ashby api
            logger.debug("parsed application no github")
            parsed_applicant["resume"] = ""
            self.applications.append(applicant)
            return
        
        # Get resume link
        logger.debug("Getting resume")
        resume_handle = applicant["resumeFileHandle"]["handle"]
        parsed_applicant["resume"] = self.client.get_resume_data(resume_handle)
        self.applications.append(parsed_applicant)
        logger.debug("Fully parsed application")
        return

    def _process_non_tech_application(self, applicant, candidate_id, application_id) -> None:
        parsed_applicant = {}
        parsed_applicant['cand_id'] = candidate_id
        parsed_applicant['app_id'] = application_id
        parsed_applicant["name"] = applicant["name"]
        
        # Get resume link
        resume_handle = applicant["resumeFileHandle"]["handle"]
        parsed_applicant["resume"] = self.client.get_resume_data(resume_handle)
        self.applications.append(parsed_applicant)
        return
