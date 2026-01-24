"""
Lead Recruiter Agent Graph - Squad 1's Workspace

This agent handles:
- CV parsing and analysis
- Skill extraction from resumes
- Candidate ranking and scoring

TODO for Squad 1:
- Implement CV parsing tools
- Add skill extraction logic
- Build ranking algorithms
- Integrate with vector store for semantic search
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage

from agents.shared.state import AgentState
from agents.shared.utils import logger, extract_last_message

# Import tools from the tools folder
from .tools.parsers import cv_parser_tool, text_cleaner_pipeline, anonymizer_tool
from .tools.extraction import skill_extractor_tool, candidate_summarizer
from .tools.ranking import similarity_matcher_tool, match_explainer, cv_ranker
from .tools.scraping import job_scraper_tool

# List of all available tools for this agent
# Bind these to your LLM: llm_with_tools = llm.bind_tools(RECRUITER_TOOLS)
RECRUITER_TOOLS = [
    cv_parser_tool,
    text_cleaner_pipeline,
    anonymizer_tool,
    skill_extractor_tool,
    candidate_summarizer,
    similarity_matcher_tool,
    match_explainer,
    cv_ranker,
    job_scraper_tool,
]


def agent_node(state: AgentState) -> dict:
    """
    Main processing node for the Lead Recruiter Agent.
    
    Args:
        state: The current agent state containing messages and job context.
    
    Returns:
        Updated state with the agent's response.
    
    TODO: Replace this mock implementation with actual CV processing logic.
    """
    # Extract the last user message for context
    last_message = state["messages"][-1] if state["messages"] else None
    user_query = last_message.content if last_message else "No query provided"
    
    # Mock response - Squad 1 will replace this with actual logic
    response_content = (
        f"🎯 **Lead Recruiter Agent Processing**\n\n"
        f"Received task: {user_query}\n\n"
        f"**Capabilities (to be implemented):**\n"
        f"- CV Parsing & Analysis\n"
        f"- Skill Extraction\n"
        f"- Candidate Ranking\n"
        f"- Resume Screening\n\n"
        f"*Squad 1: Implement your logic here!*"
    )
    
    return {
        "messages": [AIMessage(content=response_content)],
        "job_context": state.get("job_context", {})
    }


def build_recruiter_graph() -> StateGraph:
    """
    Builds and compiles the Lead Recruiter Agent graph.
    
    Returns:
        A compiled StateGraph ready for execution.
    """
    # Initialize the graph with shared state
    graph = StateGraph(AgentState)
    
    # Add the main processing node
    graph.add_node("recruiter_process", agent_node)
    
    # Set entry point
    graph.set_entry_point("recruiter_process")
    
    # Add edge to END
    graph.add_edge("recruiter_process", END)
    
    return graph.compile()


# Expose the compiled graph for import by the supervisor
recruiter_graph = build_recruiter_graph()
