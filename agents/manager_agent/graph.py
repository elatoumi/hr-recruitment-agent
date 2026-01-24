"""
Hiring Manager Agent Graph - Squad 2's Workspace

This agent handles:
- RAG-based template retrieval
- Job offer generation
- Email drafting for candidates
- Interview scheduling communications

TODO for Squad 2:
- Implement RAG pipeline for templates
- Add job offer generation logic
- Build email drafting capabilities
- Integrate with document store
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage

from agents.shared.state import AgentState
from agents.shared.utils import logger, extract_last_message

# Import tools from the tools folder
from .tools.retrieval import template_retriever_tool
from .tools.generation import job_offer_generator, offer_validator_tool, market_salary_check

# List of all available tools for this agent
# Bind these to your LLM: llm_with_tools = llm.bind_tools(MANAGER_TOOLS)
MANAGER_TOOLS = [
    template_retriever_tool,
    job_offer_generator,
    offer_validator_tool,
    market_salary_check,
]


def agent_node(state: AgentState) -> dict:
    """
    Main processing node for the Hiring Manager Agent.
    
    Args:
        state: The current agent state containing messages and job context.
    
    Returns:
        Updated state with the agent's response.
    
    TODO: Replace this mock implementation with actual template/offer generation.
    """
    # Extract the last user message for context
    last_message = state["messages"][-1] if state["messages"] else None
    user_query = last_message.content if last_message else "No query provided"
    
    # Get any shared context from the recruiter agent
    job_context = state.get("job_context", {})
    
    # Mock response - Squad 2 will replace this with actual logic
    response_content = (
        f"📝 **Hiring Manager Agent Processing**\n\n"
        f"Received task: {user_query}\n\n"
        f"**Capabilities (to be implemented):**\n"
        f"- RAG Template Retrieval\n"
        f"- Job Offer Generation\n"
        f"- Email Drafting\n"
        f"- Interview Communications\n\n"
        f"**Shared Context:** {job_context if job_context else 'No context yet'}\n\n"
        f"*Squad 2: Implement your logic here!*"
    )
    
    return {
        "messages": [AIMessage(content=response_content)],
        "job_context": job_context
    }


def build_manager_graph() -> StateGraph:
    """
    Builds and compiles the Hiring Manager Agent graph.
    
    Returns:
        A compiled StateGraph ready for execution.
    """
    # Initialize the graph with shared state
    graph = StateGraph(AgentState)
    
    # Add the main processing node
    graph.add_node("manager_process", agent_node)
    
    # Set entry point
    graph.set_entry_point("manager_process")
    
    # Add edge to END
    graph.add_edge("manager_process", END)
    
    return graph.compile()


# Expose the compiled graph for import by the supervisor
manager_graph = build_manager_graph()
