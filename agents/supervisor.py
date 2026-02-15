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
from agents.shared.utils import get_llm, logger, trim_messages
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

1. **Lead_Recruiter**: ONLY for CV/resume and web-scraping tasks:
   - Parsing and analyzing CVs/resumes (PDF, DOCX, images)
   - Summarizing candidate profiles from uploaded CVs
   - Extracting skills from CVs
   - Ranking and scoring candidates against a job description
   - Scraping job postings from a URL (LinkedIn, Indeed)
   - Semantic search across uploaded CVs

2. **Hiring_Manager**: For ALL content-generation and communication tasks:
   - Writing / generating job offers and job descriptions
   - Retrieving job-offer templates (RAG)
   - Drafting emails to candidates (offer, rejection, interview invitation)
   - Checking market salary ranges
   - Validating generated offers

CRITICAL ROUTING RULES (follow strictly):
- "generate/write/create a job offer/description" → Hiring_Manager (NEVER Lead_Recruiter)
- "draft an email / offer letter / rejection" → Hiring_Manager
- "check salary / market rate" → Hiring_Manager
- "parse / analyze / read this CV" → Lead_Recruiter
- "rank / score candidates" → Lead_Recruiter
- "scrape this URL / job posting" → Lead_Recruiter
- "search CVs for ..." → Lead_Recruiter

Multi-step workflows (route agents in sequence):
  • "generate a job offer based on this LinkedIn URL"
    → First Lead_Recruiter (scrape the URL)
    → Then Hiring_Manager (generate the offer from scraped data)
  • "parse this CV and draft a rejection email"
    → First Lead_Recruiter (parse CV)
    → Then Hiring_Manager (draft email)

Decision rules:
- Route to EXACTLY ONE agent per turn.
- Only route to Lead_Recruiter when the task explicitly involves a CV file, candidate data, or a URL to scrape.
- If the user simply asks to generate/write a job offer (no URL, no CV), route DIRECTLY to Hiring_Manager.
- After an agent finishes, if the overall task is done, respond with FINISH.
- If the message is a greeting or general question, respond with FINISH.
- NEVER route to the same agent twice in a row for the same sub-task.
"""


MAX_HOPS = 3  # Safety limit to prevent infinite loops


def _count_routing_messages(messages: list) -> int:
    """Count how many supervisor routing messages exist (i.e. how many hops so far)."""
    return sum(
        1 for m in messages
        if isinstance(m, AIMessage) and isinstance(m.content, str) and "Supervisor Decision" in m.content
    )


def _last_routed_agent(messages: list) -> str | None:
    """Return the name of the last agent that was routed to (or None)."""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and isinstance(m.content, str) and "Supervisor Decision" in m.content:
            if "Lead_Recruiter" in m.content:
                return "Lead_Recruiter"
            if "Hiring_Manager" in m.content:
                return "Hiring_Manager"
    return None


def supervisor_node(state: AgentState) -> dict:
    """
    The main supervisor node that decides routing.
    
    This node analyzes the conversation and determines which
    sub-agent should handle the next step.  It loops back after
    each agent finishes, enabling multi-hop workflows
    (e.g. scrape job → generate offer).
    
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

    # Trim messages to stay within token budget
    messages = trim_messages(messages)

    # Safety: force FINISH after MAX_HOPS agent invocations
    hops = _count_routing_messages(messages)
    if hops >= MAX_HOPS:
        logger.warning(f"Max hops ({MAX_HOPS}) reached – forcing FINISH")
        return {
            "next": "FINISH",
            "messages": [AIMessage(
                content=f"🔀 **Supervisor Decision**: Routing to `FINISH`\n*Reasoning: Max {MAX_HOPS} agent hops reached.*"
            )]
        }

    llm = get_llm()
    structured_llm = llm.with_structured_output(RouteDecision, method="json_mode")
    
    # Create the prompt chain – append JSON instruction so model outputs valid JSON
    json_instruction = (
        "\n\nRespond ONLY with a JSON object matching this schema:\n"
        '{{"next": "Lead_Recruiter" | "Hiring_Manager" | "FINISH", "reasoning": "<brief explanation>"}}\n'
        "Do not add any text outside the JSON object."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUPERVISOR_SYSTEM_PROMPT + json_instruction),
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

    # Prevent routing to the same agent twice in a row → force FINISH
    if route != "FINISH":
        prev = _last_routed_agent(messages)
        if prev and prev == route:
            logger.info(f"Same agent ({route}) twice in a row – forcing FINISH")
            route = "FINISH"
            reasoning = "Task already handled by this agent; finishing."

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
    
    # Agents loop back to supervisor for multi-hop workflows
    graph.add_edge("recruiter", "supervisor")
    graph.add_edge("manager", "supervisor")
    # Only the finish node terminates the graph
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
