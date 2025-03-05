import json
import requests
import os

url = os.getenv("APP_URL", "http://localhost:8000")
resume_analysis_url = url + "/resume_analysis"
resume_analysis_folder = "test/integration/data/resume_analysis"


class Test_WebHook:
    @classmethod
    def setup_class(cls):
        cls.url = resume_analysis_url
        cls.folder = resume_analysis_folder

    def test_example_webhook(self):
        with open(f"{self.folder}/webhook_sample.json", 'r') as file:
            data = json.load(file)
        response = requests.post(self.url, json=data)
        assert response.status_code == 200
        print(response.json())

