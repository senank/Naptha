import requests
import os

from ..states.subgraph_states import AnalysisState, GraderOutput
from ..states.main_states import AgentState
from ..prompts import job_grader
from ..models import get_model

from logging import getLogger

logger = getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"

def route_analysis(state: AnalysisState):
    if state['is_valid']:
        return "passed"
    return "failed"

# STEP 1
def validate_github(state: AnalysisState):
    if not _check_user_exists(state['github_username']):
        return {"is_valid": False}
    if not _check_contribution_count(state['github_username']):
        return {"is_valid": False}
    return {"is_valid": True}


def check_user_exists(username):
    response = requests.get(f"{GITHUB_API_BASE}/users/{username}")
    return response.status_code == 200


def check_contribution_count(username):  # TODO: Check this works and set PATToken in env
    url = GITHUB_API_BASE + "/graphql"
    headers = {
        "Authorization": f"Bearer {os.getenv("PATToken")}",
        "Content-Type": "application/json"
    }

    query = {
        "query": f"""
        {{
            user(login: "{username}") {{
                contributionsCollection {{
                    contributionCalendar {{
                        totalContributions
                    }}
                }}
            }}
        }}
        """
    }

    response = requests.post(url, headers=headers, json=query)
    if response.status_code == 200:
        data = response.json()
        total_contributions = data['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']
        logger.info(f"User {username} has made {total_contributions} contributions in the past year.")
        return total_contributions > 2
    logger.error(f"Failed to fetch contributions for {username}: {response.status_code}")
    return None


# STEP 2
def assess_candidate(state: AnalysisState):

    prompt = job_grader.format(job_name=state['job_name'],
                                job_info=state['job_info'],)
    model = get_model()
    response = model.with_structured_output(GraderOutput).invoke(prompt)
    return {
        "final_score": response.final_score
    }


# Final state
def subgraph_output_node(state: AnalysisState) -> AgentState:
    pass