"""
classify_client.py
==============

Definition of the daily summary workflow for a LangGraph agent.

This file defines the structure and flow of the daily summary process using LangGraph's 
StateGraph. The workflow is composed of multiple nodes representing discrete steps in 
the process (e.g., preprocessing, generating importance scores, and creating a summary). 
Conditional edges between nodes determine the sequence of operations and handle branching 
logic based on validation outcomes.

Functions:
    - get_client_classification_agent(): Constructs and compiles the daily summary workflow graph.

Dependencies:
    - LangGraph: For defining the StateGraph and managing workflow states and transitions.
    - resume_analysis_utils.nodes: Provides the functions for the individual nodes in the workflow.
    - resume_analysis_utils.states: Defines the input and agent states used in the workflow.

Usage:
    This module is typically invoked by the Flask endpoint `/daily_summary` in `app.py` 
    to process daily summary requests.
"""

from langgraph.graph import START, END, StateGraph
from langgraph.constants import Send

from .resume_analysis_utils.states.main_states import AgentState, InputState,\
    OutputState
from .resume_analysis_utils.states.subgraph_states import AnalysisState

from .resume_analysis_utils.nodes.main_nodes import preprocessor, output_node,\
    initiate_analysis_nodes
from .resume_analysis_utils.nodes.subgraph_nodes import validate_github, route_analysis,\
    assess_candidate, subgraph_output_node



import logging
from typing import List

logger = logging.getLogger(__name__)

def get_resume_analysis_agent():
    """
    Constructs and compiles the daily summary workflow for the LangGraph agent.

    Workflow Nodes:
        - preprocessor: Handles preprocessing of input data before other steps.
        - classify_article: Scores articles for relevance using a language model and validates the importance score based on justifications.

    Workflow Edges:
        - From `START` to `preprocessor`: Initializes the workflow.
        - Conditional edge from `preprocessor` to `initiate_classification_nodes`:
            Executes `classify_article` in parellel for all importance nodes.
        - From `classify_article` to `END`: Terminates the workflow.
        
    Returns:
        StateGraph: A compiled workflow graph ready for invocation by the LangGraph agent.
    
    NOTES:
    - InputState is the input data for the agent, and AgentState is the output/overall data from the agent.

    Example Usage:
        agent = get_client_classification_agent()
        result = agent.invoke(ClassificationInputState(data))
    """
    logger.info("Constructing daily summary workflow")
    workflow = StateGraph(AgentState, input=InputState, output=OutputState)
    
    # Add nodes
    logger.debug("Adding nodes and edges to the workflow")
    workflow.add_node("preprocessor", preprocessor)
    workflow.add_node("create_analysis_subgraph", create_analysis_subgraph())
    workflow.add_node("output_node", output_node)

    # Add edges
    logger.debug("Adding edges to the workflow")
    workflow.add_edge(START, "preprocessor")
    workflow.add_conditional_edges("preprocessor", initiate_analysis_nodes, ["create_analysis_subgraph"]) # ? Will remove

    workflow.add_edge("create_analysis_subgraph", "output_node")
    workflow.add_edge("output_node", END)

    logger.info("Workflow construction complete")
    return workflow.compile()

def create_analysis_subgraph():
    logger.info("Constructing subgraph for classification")
    workflow = StateGraph(AnalysisState)
    workflow.add_node("step_1", validate_github)
    workflow.add_node("step_2", assess_candidate)
    workflow.add_node("subgraph_output_node", subgraph_output_node)
    
    # workflow.add_edge(START, "classify_article")
    workflow.add_conditional_edges("step_1", 
                                    route_analysis, 
                                   {
                                        "passed": "step_2",
                                        "failed": "subgraph_output_node"
                                   }
                                )
    workflow.add_edge("step_2", "subgraph_output_node")

    workflow.set_entry_point("step_1")
    workflow.set_finish_point("subgraph_output_node")
    return workflow.compile()

graph = get_resume_analysis_agent()