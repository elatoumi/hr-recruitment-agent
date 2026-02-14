"""
Supervisor Agent - Hierarchical Router for Multi-Agent System

This module implements the Supervisor Pattern that routes tasks between:
- Lead Recruiter Agent (CV parsing, skill extraction, ranking)
- Hiring Manager Agent (RAG templates, job offers, emails)

The supervisor uses an LLM to analyze user intent and route appropriately.
"""

from typing import Literal
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agents.shared.state import AgentState
from agents.shared.utils import get_llm, logger
from agents.recruiter_agent import recruiter_graph
from agents.manager_agent import manager_graph


# Define the possible routing destinations
TEAM_MEMBERS = ["Lead_Recruiter", "Hiring_Manager"]
FINISH = "FINISH"


class RouteDecision(BaseModel):
    """
    Pydantic model for structured routing decisions.
    Used with LLM's with_structured_output for reliable parsing.
    """
    next: Literal["Lead_Recruiter", "Hiring_Manager", "FINISH"] = Field(
        description="The next agent to route to, or FINISH if the task is complete."
    )
    reasoning: str = Field(
        description="Brief explanation of why this routing decision was made."
    )


# System prompt for the supervisor
SUPERVISOR_SYSTEM_PROMPT = """You are a supervisor managing a recruitment team with two specialized agents:

1. **Lead_Recruiter**: Handles CV/resume tasks including:
   - Parsing and analyzing CVs/resumes (PDF, DOCX, etc.)
   - Summarizing candidate profiles
   - Extracting skills from candidates
   - Ranking and scoring candidates
   - Scraping job boards or profiles
   - Screening applications

2. **Hiring_Manager**: Handles communication and documentation tasks including:
   - Writing job offers and descriptions
   - Retrieving templates (RAG)
   - Drafting emails to candidates
   - Creating interview invitations
   - Generating offer letters

Based on the user's request, decide which agent should handle the task.
If the task appears complete or is a simple greeting/question, respond with FINISH.
"""


def supervisor_node(state: AgentState) -> dict:
    """
    The main supervisor node that decides routing.
    
    This node analyzes the conversation and determines which
    sub-agent should handle the next step.
    
    Args:
        state: Current agent state with messages and context.
    
    Returns:
        Updated state with routing decision.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return {
            "next": "FINISH",
            "messages": [AIMessage(content="No input received. Please provide a task.")]
        }
        
    llm = get_llm()
    structured_llm = llm.with_structured_output(RouteDecision)
    
    # Create the prompt chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUPERVISOR_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | structured_llm
    
    try:
        decision = chain.invoke({"messages": messages})
        route = decision.next
        reasoning = decision.reasoning
    except Exception as e:
        logger.error(f"Supervisor LLM error: {e}")
        # Fallback to FINISH if LLM fails
        route = "FINISH" 
        reasoning = "Error in decision making process."

    # Log the routing decision
    routing_message = AIMessage(
        content=f"🔀 **Supervisor Decision**: Routing to `{route}`\n*Reasoning: {reasoning}*"
    )
    
    return {
        "next": route,
        "messages": [routing_message]
    }


def recruiter_node(state: AgentState) -> dict:
    """
    Wrapper node that invokes the Lead Recruiter sub-graph.
    """
    # Invoke the recruiter sub-graph
    result = recruiter_graph.invoke(state)
    return {
        "messages": result.get("messages", []),
        "job_context": result.get("job_context", state.get("job_context", {}))
    }


def manager_node(state: AgentState) -> dict:
    """
    Wrapper node that invokes the Hiring Manager sub-graph.
    """
    # Invoke the manager sub-graph
    result = manager_graph.invoke(state)
    return {
        "messages": result.get("messages", []),
        "job_context": result.get("job_context", state.get("job_context", {}))
    }


def finish_node(state: AgentState) -> dict:
    """
    Terminal node for when no agent routing is needed.
    """
    messages = state.get("messages", [])
    
    # Check if we already have a response
    if len(messages) <= 2:  # Only user message + routing message
        return {
            "messages": [AIMessage(
                content="👋 Hello! I'm your HR Recruitment Assistant.\n\n"
                "I can help you with:\n"
                "- **CV Analysis & Ranking** → Lead Recruiter\n"
                "- **Job Offers & Templates** → Hiring Manager\n\n"
                "What would you like to do today?"
            )]
        }
    return {}


def route_to_agent(state: AgentState) -> str:
    """
    Conditional edge function that returns the next node based on state.
    
    Args:
        state: Current agent state.
    
    Returns:
        The name of the next node to execute.
    """
    next_step = state.get("next", "FINISH")
    
    if next_step == "Lead_Recruiter":
        return "recruiter"
    elif next_step == "Hiring_Manager":
        return "manager"
    else:
        return "finish"


def build_supervisor_graph() -> StateGraph:
    """
    Builds and compiles the main supervisor graph.
    
    Returns:
        A compiled StateGraph implementing the hierarchical supervisor pattern.
    """
    # Initialize the graph with shared state
    graph = StateGraph(AgentState)
    
    # Add all nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("recruiter", recruiter_node)
    graph.add_node("manager", manager_node)
    graph.add_node("finish", finish_node)
    
    # Set the entry point
    graph.set_entry_point("supervisor")
    
    # Add conditional edges from supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "recruiter": "recruiter",
            "manager": "manager",
            "finish": "finish"
        }
    )
    
    # All agents route back to END after processing
    graph.add_edge("recruiter", END)
    graph.add_edge("manager", END)
    graph.add_edge("finish", END)
    
    return graph.compile()


# Export the compiled supervisor graph
supervisor_graph = build_supervisor_graph()


# Convenience function for running the graph
def run_supervisor(user_input: str, job_context: dict = None) -> dict:
    """
    Convenience function to run the supervisor graph with a user input.
    
    Args:
        user_input: The user's message/request.
        job_context: Optional shared context dictionary.
    
    Returns:
        The final state after graph execution.
    """
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "next": "",
        "job_context": job_context or {}
    }
    
    return supervisor_graph.invoke(initial_state)
