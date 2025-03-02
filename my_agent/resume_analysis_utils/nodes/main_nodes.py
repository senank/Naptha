"""
classify_client_utils/nodes.py
====================

Implementation of LangGraph nodes for the client analysis summary workflow.

This file defines the core nodes (functions) used in the client analysis workflow 
managed by LangGraph. Each node represents a discrete step in the workflow, 
executed as part of a `StateGraph`. The nodes perform tasks such as data preprocessing, 
importance scoring, data selection, summary generation, and validation.

Nodes Defined:
    - Preprocessor Node:
        - `preprocessor(state: InputState) -> AgentState`: Extracts and prepares input data, 
          initializing fields such as client info, articles, and scoring placeholders.

    - Classification Nodes:
        - `initiate_analysis_nodes(state: AgentState)`: Creates a "map step" to run 
          `classify_article` on multiple articles using the Send API.
        - `classify_article(state: ClassificationState)`: Scores articles for relevance using 
          a language model and validates the importance score based on justifications.

Dependencies:
    - LangGraph: Provides the `Send` API and manages the workflow.
    - LangChain-based utilities: Language model instances are used for scoring, generation, 
      and validation of content.
    - Custom Prompts: The workflow relies on predefined prompts to guide each model invocation.

Purpose:
    These nodes are designed to facilitate the analysis of the main subject of a given article. 
    They interact with external language models (e.g., OpenAI models) and ensure robust processing 
    through retries, validations, and scoring mechanisms.

Usage:
    The nodes are used within a `StateGraph` (e.g., in `classify_client.py`) to define and 
    execute the workflow. They are invoked in sequence or in parallel, depending on the 
    edges connecting them in the graph.

Example Workflow Integration:
    ```
    from classify_client_utils.nodes import preprocessor, generate_importance, selector

    workflow.add_node("preprocessor", preprocessor)
    workflow.add_node("generate_importance", generate_importance)
    workflow.add_node("selector", selector)
    ```
"""

# Imports
from ..states.main_states import AgentState, InputState, OutputState
from ..states.subgraph_states import AnalysisState
# from .prompts import
from ..models import get_model
from ...externals import get_resumes, send_classified_resumes
from ...constants import JSON_JOB_INFO, JSON_JOB_NAME

from typing import List

from langgraph.constants import Send

### Nodes Implementation ###
# Preprocessor Node
def preprocessor(state: InputState) -> AgentState:
    """
    Preprocesses the input state and initializes the overall workflow state.

    This node extracts data from the input state, including client information, 
    output preferences, and articles to be processed. It also initializes empty 
    fields for scores, selected articles, the summary, and the regeneration count.

    Args:
        state (InputState): The input state containing raw data for the workflow,
            such as client information and articles.

    Returns:
        AgentState: The initialized workflow state, with pre-filled client information,
            output style, and placeholders for scores, selected articles, and summary.
    
    Workflow Initialization:
        - Extracts `client_name`, `client_info`, `output_style`, and `articles` from the input state.
        - Sets up empty lists for scores (`score_1` through `score_5`).
        - Initializes `articles_to_include` as an empty list.
        - Sets `summary` as an empty string.
        - Initializes `regeneration_count` to 0.
    
    Example:
        InputState:
            {
                "client_name": "Client A",
                "client_info": "Details about Client A",
                "output_style": "2 headings, bullet points",
                "articles": ["Article 1", "Article 2"]
            }
        Output AgentState:
            {
                "client_name": "Client A",
                "client_info": "Details about Client A",
                "output_style": "2 headings, bullet points",
                "articles": ["Article 1", "Article 2"],
                "score_1": [],
                "score_2": [],
                "score_3": [],
                "score_4": [],
                "score_5": [],
                "articles_to_include": [],
                "summary": "",
                "regeneration_count": 0
            }
    """
    job_name = state.get(JSON_JOB_NAME, "")
    job_info = state.get(JSON_JOB_INFO, "")
    resumes = state.get("resumes", [])
    return AgentState(
        job_name = job_name,
        job_info = job_info,
        resumes = resumes,
        analysis = [],
    )


def initiate_analysis_nodes(state: AgentState) -> List[Send]:
    """
    Creates tasks for the analysis of the subjects for the given article(s).

    This function acts as a "map step" in the workflow, generating a list of tasks 
    for determining the subject of each article in the `articles` field of the `AgentState`. 
    Each task is configured to use the `classify_article` node via the Send API.

    Args:
        state (AgentState): The current workflow state containing the articles to process.

    Returns:
        List[Send]: A list of tasks to be executed for scoring article importance, 
        where each task contains the client name, client info, and article ID.

    Example:
        Input AgentState:
            {
                "client_name": "Client A",
                "client_info": "Some client details",
                "articles": ["article_1", "article_2"]
            }
        Output:
            [
                Send("generate_importance", {
                    "client_name": "Client A",
                    "client_info": "Some client details",
                    "article_id": "article_1"
                }),
                Send("generate_importance", {
                    "client_name": "Client A",
                    "client_info": "Some client details",
                    "article_id": "article_2"
                })
            ]
    """
    resumes = state['resumes']
    return [
        Send("create_analysis_subgraph", AnalysisState( #create_analysis_subgraph(article)
                # TODO
            )
        ) for resume in resumes
    ]


def output_node(state: AgentState) -> OutputState:
    pass  # TODO
