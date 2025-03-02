"""
classify_client_utils/models.py
=====================

Utility functions for initializing OpenAI models with LangChain.

This file provides utility functions for creating instances of OpenAI models using 
the LangChain `ChatOpenAI` class. These functions abstract the initialization of 
models with configurable parameters like temperature and response format.

Functions:
    - get_model(temperature=0, model='gpt-4o'): Creates a standard `ChatOpenAI` instance 
      for text-based tasks with configurable temperature and model type.
    - get_json_model(temperature=0, model='gpt-4o'): Creates a `ChatOpenAI` instance 
      configured to return JSON-formatted responses.

Dependencies:
    - langchain_openai: Provides the `ChatOpenAI` class used for creating model instances.

Usage:
    These utility functions can be imported and used to create model instances for 
    LangGraph workflows or other integrations requiring OpenAI models.

Example:
    ```
    from my_agent.classify_client_utils.models import get_model

    # Initialize a standard text model
    model = get_model(temperature=0.5, model='gpt-4o')
    model.invoke("What is the capital of France?")
    model.with_structured_output(MyOutputStruct).invoke("What is the capital of France?")
    ```
"""
# imports
from langchain_openai import ChatOpenAI

def get_model(temperature=0, model='gpt-4o'):
    """
    Initializes a ChatOpenAI instance for text-based tasks.

    Args:
        temperature (float): Controls the randomness of the model's output (default: 0).
        model (str): The name of the model to use (default: 'gpt-4o').

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI model.
    """
    return ChatOpenAI(
        model=model,
        temperature = temperature,
    )

