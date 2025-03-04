"""
classify_client_utils/states.py 
=====================

Definitions of state objects for the client classification workflow.

This file contains type definitions and Pydantic models representing the various states 
used throughout the LangGraph-based client classification workflow. These states capture the input, 
intermediate, and output data at different stages of the workflow, ensuring type safety 
and validation during processing.

Classes:
    - `InputState`: A `TypedDict` representing the input to the first node of the workflow, 
      including client information, articles, and output preferences.
    - `AgentState`: A `TypedDict` capturing the overall state of the workflow, 
      tracking scores, selected articles, the summary, and other intermediate data.
    - `OutputState`: A `TypedDict` representing the output of the final node in the workflow,
      including the client name and the final classification of articles.
    - `ClassificationState`: A `BaseModel` defining the intermediate state of the classification process,
    - `ClassificationOutput`: A `BaseModel` defining the output of the classification process,
    - `ClassificationValidationOutput`: A `BaseModel` defining the output of the classification validation process.
Purpose:
    These state definitions facilitate structured data flow within the LangGraph workflow. 
    They are used to define node inputs and outputs, enforce validation rules, and maintain 
    consistency across the workflow.

Dependencies:
    - `typing`: Provides type annotations like `List`, `TypedDict`, and `Annotated` for 
      flexible state definitions.
    - `pydantic`: Enables robust data validation and serialization using `BaseModel`.
    - `LangGraph`: Utilizes these states to track workflow progress and manage node transitions.

Usage:
    Import the required state objects in the workflow or node definitions to define inputs 
    and outputs for LangGraph nodes.

Example:
    ```
    from classify_client_utils.states import AgentState, ImportanceInput

    def preprocessor(state: InputState) -> AgentState:
        # Process the input data and return the initial AgentState
        ...
    ```
"""

# Imports
from typing import List, TypedDict, Tuple, Annotated, Literal, Dict
from operator import add

### Input state ###
class InputState(TypedDict):
    """
    Represents the input state for the first node in the client classification workflow.

    Attributes:
        client_name (str): The name of the client for whom the summary is being generated.
        client_info (str): Additional information about the client.
        articles (List[str]): A list of articles to be processed in the workflow.
    """
    job_name: str
    job_info: str
    application_data: List[Dict]

### Overall state ###
class AgentState(TypedDict):  # TODO: states: Define AgentState
    """
    Represents the overall state of the workflow graph during execution.

    Attributes:
        client_name (str): The name of the client to determine if they are the main subject.
        client_info (str): Additional information about the client.
        output_style (str): The desired style or format of the summary output.
        articles (List[str]): A list of articles being processed in the workflow.
        classification (List[Tuple[str, str]]): The classification of main subject of articles.
    """
    job_name: str
    job_info: str
    resumes: List[Dict]
    classification: Annotated[List[Tuple[str, bool]], add]

### Output state ###
class OutputState(TypedDict):  # TODO: states: Determine OutputState
    """
    Represents the output state for the final node in the client classification workflow.

    Attributes:
        client_name (str): The name of the client for whom the summary was generated.
        classification (List[Tuple[str, str]]): The final classification of articles
    """
    job_name: str
    classification: List[Tuple[str, bool]]

