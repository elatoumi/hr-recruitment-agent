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
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage

from agents.shared.state import AgentState
from agents.shared.utils import logger, get_llm

# Import tools from the tools folder
from .tools.retrieval import template_retriever_tool
from .tools.generation import job_offer_generator, offer_validator_tool, market_salary_check

# List of all available tools for this agent
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
    """
    llm = get_llm()
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(MANAGER_TOOLS)
    
    # Invoke the LLM with the message history
    response = llm_with_tools.invoke(state["messages"])
    
    return {"messages": [response]}


def build_manager_graph() -> StateGraph:
    """
    Builds and compiles the Hiring Manager Agent graph.
    
    Returns:
        A compiled StateGraph ready for execution.
    """
    # Initialize the graph with shared state
    graph = StateGraph(AgentState)
    
    # Add the main agent node
    graph.add_node("manager_process", agent_node)
    
    # Add the tool execution node
    tool_node = ToolNode(MANAGER_TOOLS)
    graph.add_node("tools", tool_node)
    
    # Set entry point
    graph.set_entry_point("manager_process")
    
    # Define conditional logic
    # If the LLM produces tool calls -> 'tools' node
    # Otherwise -> END
    graph.add_conditional_edges(
        "manager_process",
        tools_condition,
    )
    
    # Return from tools back to agent to generate final response
    graph.add_edge("tools", "manager_process")
    
    return graph.compile()


# Expose the compiled graph for import by the supervisor
manager_graph = build_manager_graph()
