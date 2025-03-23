import requests

from typing import Dict, List
from logging import getLogger
from time import time

from io import BytesIO
from PyPDF2 import PdfReader

logger = getLogger(__name__)
from .constants import ASHBY_API_KEY, ASHBY_API_URL, ASHBY_SCORE_FIELD_ID, TECH_JOBS

class SyncToken:
    _sync_token = None  # ? TODO: data: Determine if sync token lasts for all queries
    _next_cursor = None  # ? TODO: data: Determine if cursor lasts for all queries
    _last_updated = None

    @classmethod
    def get_sync_token(cls):
        if not cls._last_updated:
            return None, None
        if not cls._valid_time_difference():
            return None, None
        return cls.sync_token, cls.next_cursor
    
    @classmethod
    def set_sync_token(cls, token, cursor):
        cls.sync_token = token
        cls._last_updated = time()
        cls._next_cursor = cursor

    @classmethod
    def _valid_time_difference(cls):
        difference_in_secs = (time() - cls._last_updated) 
        difference_in_days = difference_in_secs / (60 * 60 * 24)
        return difference_in_days <= 6

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
        pass

    def _fetch_job_applications(self, job_posting_id: str):
        """
        Gets all new job applications based on job_posting_id and last request.
        
        Uses sync token to track the state of all requested, and next cursor to
        track where the last request left off.
        """
        url = self.api_url + "/application.list"
        payload = {
            "limit": 50,  # ? TODO: data: Consider size of data and why limit is 50
            "jobId": job_posting_id
        }

        data = []
        sync_token, next_cursor = SyncToken.get_sync_token()
        if sync_token:  # Checks if already synced
            # ?: data: MUST BE CALLED ATLEAST ONCE PER 6 DAYS OR SYNC TOKEN EXPIRES
            payload['syncToken'] = sync_token
        
        if next_cursor:  # Checks where left off
            payload['nextCursor'] = next_cursor
        
        try:
            while True:  # Get all new applications (payload specifies job_id)
                # TODO: data: make this async; consider the payload data aswell
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
                    logger.error("Failed respons in _send_request_to_ashby")
                
                data += response.json()['results']
                
                sync_token = response.get("syncToken", None)
                next_cursor = response.get("nextCursor", "")
                
                if sync_token:
                    payload["syncToken"] = sync_token
                payload["nextCursor"] = next_cursor
                
                if response["moreDataAvailable"] == False:  # If there is more loop again
                    break
            SyncToken.set_sync_token(sync_token, next_cursor)
            return data
        except Exception as e:
            logger.error(f"_send_request_to_ashby: {e}")

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
        return _send_request_to_ashby(url, payload)

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
        for application in applications:
            self._process_application(application, job_name)
    
    def _process_application(self, application, job_name) -> None:
        if application['status'] != "Active":
            return

        if application["currentInterviewStage"]["type"] != "PreInterviewScreen":  #? what is needed to not consider application
            return

        cand_id = application['candidate']['id']
        app_id = application['id']
        applicant = self.client.get_applicant_info(cand_id)
        if job_name in TECH_JOBS:
            self._process_tech_applicant(applicant, cand_id, app_id)
        else:
            self._process_non_tech_application(applicant, cand_id, app_id)
        return
        
    def _process_tech_applicant(self, applicant, candidate_id, application_id) -> None:
        parsed_applicant = {}
        parsed_applicant['cand_id'] = candidate_id
        parsed_applicant['app_id'] = application_id
        parsed_applicant["name"] = applicant["name"]
        parsed_applicant["github"] = ""
        
        # get github username
        for link in applicant["socialLinks"]:
            if link["type"] == "GitHub":
                parsed_applicant["github"] = link["url"].rstrip("/").split("/")[-1]
                break
            
        if not applicant["github"]:  # prevents unneccessary calls to get resume from Ashby api
            parsed_applicant["resume"] = ""
            self.applications.append(applicant)
            return
        
        # Get resume link
        resume_handle = applicant["resumeFileHandle"]["handle"]
        parsed_applicant["resume"] = self.client.get_resume_data(resume_handle)
        self.applications.append(parsed_applicant)
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
