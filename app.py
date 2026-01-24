"""
Intelligent HR Recruitment Platform - Main Application

A Multi-Agent System (MAS) powered by LangGraph for intelligent recruitment.
Features a hierarchical supervisor pattern routing between specialized agents.
"""

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agents.supervisor import supervisor_graph


# Page configuration
st.set_page_config(
    page_title="HR Recruitment Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "job_context" not in st.session_state:
        st.session_state.job_context = {}


def render_sidebar():
    """Render the sidebar with agent information and controls."""
    with st.sidebar:
        st.header("🤖 Agent System")
        
        st.markdown("### Available Agents")
        
        # Lead Recruiter Card
        with st.expander("🎯 Lead Recruiter", expanded=True):
            st.markdown("""
            **Capabilities:**
            - CV/Resume Parsing
            - Skill Extraction
            - Candidate Ranking
            - Application Screening
            
            *Trigger words: analyze, rank, parse, CV, candidate, skill*
            """)
        
        # Hiring Manager Card
        with st.expander("📝 Hiring Manager", expanded=True):
            st.markdown("""
            **Capabilities:**
            - Job Offer Generation
            - Template Retrieval (RAG)
            - Email Drafting
            - Interview Communications
            
            *Trigger words: offer, template, email, draft, write*
            """)
        
        st.markdown("---")
        
        # Job Context Display
        st.markdown("### 📋 Current Job Context")
        if st.session_state.job_context:
            st.json(st.session_state.job_context)
        else:
            st.info("No context yet. Start a conversation!")
        
        st.markdown("---")
        
        # Controls
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.job_context = {}
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        st.success("✅ Supervisor: Online")
        st.success("✅ Lead Recruiter: Ready")
        st.success("✅ Hiring Manager: Ready")


def render_chat_interface():
    """Render the main chat interface."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Intelligent HR Recruitment Platform</h1>
        <p>Multi-Agent System powered by LangGraph</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(message.content)
    
    # Chat input
    if user_input := st.chat_input("Ask about candidates, job offers, or recruitment tasks..."):
        # Add user message to state
        user_message = HumanMessage(content=user_input)
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process through supervisor graph
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    # Prepare input state
                    input_state = {
                        "messages": [user_message],
                        "next": "",
                        "job_context": st.session_state.job_context
                    }
                    
                    # Stream/invoke the graph
                    result = supervisor_graph.invoke(input_state)
                    
                    # Extract and display responses
                    response_messages = result.get("messages", [])
                    
                    for msg in response_messages:
                        if isinstance(msg, AIMessage):
                            st.markdown(msg.content)
                            st.session_state.messages.append(msg)
                    
                    # Update job context
                    if result.get("job_context"):
                        st.session_state.job_context.update(result["job_context"])
                
                except Exception as e:
                    error_msg = f"❌ Error processing request: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(AIMessage(content=error_msg))


def render_quick_actions():
    """Render quick action buttons for common tasks."""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Analyze CVs", use_container_width=True):
            st.session_state.pending_action = "Analyze the uploaded CVs and extract key skills"
            st.rerun()
    
    with col2:
        if st.button("🏆 Rank Candidates", use_container_width=True):
            st.session_state.pending_action = "Rank the candidates based on their qualifications"
            st.rerun()
    
    with col3:
        if st.button("📝 Draft Job Offer", use_container_width=True):
            st.session_state.pending_action = "Write a job offer letter for the selected candidate"
            st.rerun()
    
    with col4:
        if st.button("✉️ Email Template", use_container_width=True):
            st.session_state.pending_action = "Get an email template for interview invitation"
            st.rerun()


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Check for pending actions from quick action buttons
    if "pending_action" in st.session_state:
        action = st.session_state.pending_action
        del st.session_state.pending_action
        
        # Add as user message
        user_message = HumanMessage(content=action)
        st.session_state.messages.append(user_message)
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    render_chat_interface()
    
    # Quick actions at the bottom
    with st.container():
        st.markdown("---")
        render_quick_actions()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888;'>"
        "Built with ❤️ using LangGraph & Streamlit | "
        "Hierarchical Supervisor Pattern"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()