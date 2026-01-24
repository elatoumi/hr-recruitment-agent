"""
Global State Protocol for the Multi-Agent System.
This defines the shared state that flows between all agents in the hierarchy.
"""

from typing import Annotated, Any, TypedDict
import operator
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    The global state shared across all agents in the system.
    
    Attributes:
        messages: A list of LangChain messages representing the conversation history.
                  Uses operator.add for automatic message accumulation.
        next: The next agent/node to route to (used by conditional edges).
        job_context: A shared dictionary for passing data between agents
                     (e.g., extracted skills, candidate IDs, job requirements).
    """
    messages: Annotated[list[BaseMessage], operator.add]
    next: str
    job_context: dict[str, Any]
