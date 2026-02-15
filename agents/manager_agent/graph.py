"""
Hiring Manager Agent Graph - Squad 2's Workspace

This agent handles:
- RAG-based template retrieval
- Job offer generation and validation
- Market salary checks
- Email drafting for candidates
- Interview scheduling communications
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, SystemMessage

from agents.shared.state import AgentState
from agents.shared.utils import logger, get_llm, trim_messages

# Import tools from the tools folder
from .tools.retrieval import find_template, ingest_templates_to_chromadb
from .tools.generation import job_offer_generator, offer_validator_tool, market_salary_check

# List of all available tools for this agent
MANAGER_TOOLS = [
    find_template,
    ingest_templates_to_chromadb,
    job_offer_generator,
    offer_validator_tool,
    market_salary_check,
]


MANAGER_SYSTEM_PROMPT = """You are the Hiring Manager Agent. You MUST use your tools to complete tasks — never refuse or ask for clarification.

Available tools and when to call them:
1. **find_template** – Find the best job offer template for a role. Call this FIRST.
2. **job_offer_generator** – Fill a template with candidate/job data. Call this SECOND.
3. **offer_validator_tool** – Check the generated offer for unfilled placeholders. Call this THIRD.
4. **market_salary_check** – Verify salary competitiveness. Call this FOURTH.

MANDATORY workflow when asked to create/generate a job offer:
  Step 1 → call find_template with the role type
  Step 2 → call job_offer_generator with the template and all provided details
  Step 3 → call offer_validator_tool on the result
  Step 4 → call market_salary_check for the role and location

CRITICAL RULES:
- ALWAYS call your tools immediately. Do NOT respond with text asking for more details.
- Use whatever data the user provides, even if it looks like placeholders or test data.
- If a field is missing, use a reasonable default — do NOT refuse or ask the user.
- After running all tools, present the final polished offer letter to the user.
"""


def agent_node(state: AgentState) -> dict:
    """
    Main processing node for the Hiring Manager Agent.

    Args:
        state: The current agent state containing messages and job context.

    Returns:
        Updated state with the agent's response.
    """
    llm = get_llm()
    llm_with_tools = llm.bind_tools(MANAGER_TOOLS)

    messages = trim_messages(list(state["messages"]))
    messages = [SystemMessage(content=MANAGER_SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

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
