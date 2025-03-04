from typing import TypedDict, Dict
from pydantic import BaseModel, Field

### Intermediate states ###
# Classification states
class AnalysisState(TypedDict):  #TODO: substate: Analysis state
    """
    Represents the intermediate state of the classification process.

    Attributes:
        client_name (str): The name of the client to determine if they are the main subject.
        article_id (str): The unique identifier for the article.
        classification (str): The classification of the article.
        regeneration_count (int): The number of times the article has been reclassified.
    """
    job_name: str
    job_info: str
    resume: Dict
    final_score: float

class GraderOutput(BaseModel):
    """
    Represents the output of the classification process.

    Attributes:
        classification (List[str]): Represents the main subjects of a given article input
    """
    technical_expertise: int
    practical_experience: int
    job_alignment: int
    final_score: float

