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
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, SystemMessage
from pathlib import Path

from agents.shared.state import AgentState
from agents.shared.utils import logger, get_llm

# Import tools from the tools folder
from .tools.parsers import cv_parser_tool, text_cleaner_pipeline, anonymizer_tool
from .tools.extraction import skill_extractor_tool, candidate_summarizer, search_cvs_by_content
from .tools.ranking import similarity_matcher_tool, match_explainer, cv_ranker
from .tools.scraping import job_scraper_tool

# List of all available tools for this agent
RECRUITER_TOOLS = [
    cv_parser_tool,
    text_cleaner_pipeline,
    anonymizer_tool,
    skill_extractor_tool,
    candidate_summarizer,
    search_cvs_by_content,
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
    """
    # Scan for uploaded files to provide context
    upload_dir = Path("data/uploads")
    file_context = ""
    if upload_dir.exists():
        files = [f.name for f in upload_dir.glob("*") if f.is_file()]
        if files:
            file_list = ", ".join([f"data/uploads/{f}" for f in files])
            file_context = (
                f"\n\nCONTEXT: The following files are available in the local storage:\n{file_list}\n"
                "If the user mentions a file name, use the full path from this list to process it."
            )

    llm = get_llm()
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(RECRUITER_TOOLS)
    
    # Prepend system message with file context
    messages = list(state["messages"])
    system_prompt = (
        "You are the Lead Recruiter Agent. "
        "Your responsibilities include parsing CVs, extracting skills, summarizing candidates, and searching for candidates by keyword/content. "
        "You leverage a RAG (Retrieval-Augmented Generation) system to semantically search across all uploaded CVs. "
        "For ANY question about candidate skills, experience, or specific text in CVS (e.g., 'Who knows Python?', 'Screen for Taher'), "
        "IMMEDIATELY use the 'search_cvs_by_content' tool."
        f"{file_context}"
    )
    
    # Add system message to the beginning of the context
    messages = [SystemMessage(content=system_prompt)] + messages

    # Invoke the LLM with the message history
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def build_recruiter_graph() -> StateGraph:
    """
    Builds and compiles the Lead Recruiter Agent graph.
    
    Returns:
        A compiled StateGraph ready for execution.
    """
    # Initialize the graph with shared state
    graph = StateGraph(AgentState)
    
    # Add the main agent node
    graph.add_node("recruiter_process", agent_node)
    
    # Add the tool execution node
    tool_node = ToolNode(RECRUITER_TOOLS)
    graph.add_node("tools", tool_node)
    
    # Set entry point
    graph.set_entry_point("recruiter_process")
    
    # Define conditional logic
    # If the LLM produces tool calls -> 'tools' node
    # Otherwise -> END
    graph.add_conditional_edges(
        "recruiter_process",
        tools_condition,
    )
    
    # Return from tools back to agent to generate final response
    graph.add_edge("tools", "recruiter_process")
    
    return graph.compile()


# Expose the compiled graph for import by the supervisor
recruiter_graph = build_recruiter_graph()
