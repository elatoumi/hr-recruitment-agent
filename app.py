"""
Intelligent HR Recruitment Platform - Main Application

A Multi-Agent System (MAS) powered by LangGraph for intelligent recruitment.
Features a hierarchical supervisor pattern routing between specialized agents.
"""

import streamlit as st
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

from agents.supervisor import supervisor_graph
from agents.shared.utils import trim_messages


st.set_page_config(
    page_title="HR Recruitment Platform",
    page_icon="🎯",
    layout="centered",
)

# Minimal styling
st.markdown("""
<style>
    .block-container { max-width: 760px; }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "job_context" not in st.session_state:
    st.session_state.job_context = {}
if "uploaded_cvs" not in st.session_state:
    st.session_state.uploaded_cvs = []
if "show_offer_form" not in st.session_state:
    st.session_state.show_offer_form = False

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────
def _extract_display_text(response_messages) -> str:
    """Return only the final substantive assistant response, skipping routing messages."""
    substantive = []
    for msg in response_messages:
        if not isinstance(msg, AIMessage):
            continue
        if not msg.content or not isinstance(msg.content, str):
            continue
        text = msg.content.strip()
        if not text:
            continue
        if text.startswith("\U0001f500") and "Supervisor Decision" in text:
            continue
        substantive.append(text)
    return substantive[-1] if substantive else ""


def _send_message(text: str):
    """Send a message through the supervisor and display the response."""
    user_message = HumanMessage(content=text)
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(text)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                input_state = {
                    "messages": trim_messages(list(st.session_state.messages)),
                    "next": "",
                    "job_context": st.session_state.job_context,
                }
                result = supervisor_graph.invoke(input_state)

                display_text = _extract_display_text(result.get("messages", []))
                if display_text:
                    st.markdown(display_text)
                    st.session_state.messages.append(AIMessage(content=display_text))
                else:
                    st.info("Done — no text response generated.")
                    st.session_state.messages.append(AIMessage(content="(task completed)"))

                if result.get("job_context"):
                    st.session_state.job_context.update(result["job_context"])

            except Exception as e:
                err = f"❌ {e}"
                st.error(err)
                st.session_state.messages.append(AIMessage(content=err))


# ── Top bar ────────────────────────────────────────────────────
col_title, col_upload, col_form_btn = st.columns([4, 4, 2])

with col_title:
    st.markdown("#### 🎯 HR Recruitment")

with col_upload:
    uploaded_files = st.file_uploader(
        "Upload CVs",
        type=["pdf", "docx", "txt", "jpg", "png"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        saved = []
        for f in uploaded_files:
            p = UPLOAD_DIR / f.name
            p.write_bytes(f.getbuffer())
            path_str = str(p)
            if path_str not in st.session_state.uploaded_cvs:
                st.session_state.uploaded_cvs.append(path_str)
            saved.append(f.name)
        st.success(f"{len(saved)} CV(s) uploaded")

with col_form_btn:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("📝 Job Offer", use_container_width=True):
        st.session_state.show_offer_form = not st.session_state.show_offer_form

# ── Job Offer Form (collapsible) ──────────────────────────────
if st.session_state.show_offer_form:
    with st.expander("📝 Job Offer Details", expanded=True):
        with st.form("job_offer_form", clear_on_submit=True):
            st.markdown("**Fill in what you have — empty fields will use smart defaults.**")

            fc1, fc2 = st.columns(2)
            with fc1:
                f_job_title = st.text_input("Job Title *", placeholder="e.g. Senior Python Developer")
                f_candidate = st.text_input("Candidate Name", placeholder="e.g. Alex Johnson")
                f_email = st.text_input("Candidate Email", placeholder="e.g. alex@example.com")
                f_salary = st.text_input("Base Salary (annual)", placeholder="e.g. $130,000")
                f_company = st.text_input("Company Name", placeholder="e.g. Acme Corp")
            with fc2:
                f_location = st.text_input("Location / Work Mode", placeholder="e.g. Remote, San Francisco — Hybrid")
                f_start_date = st.text_input("Start Date", placeholder="e.g. June 3, 2026")
                f_manager = st.text_input("Reporting Manager", placeholder="e.g. Jane Smith, VP Engineering")
                f_contact = st.text_input("HR Contact (name, email, phone)", placeholder="e.g. HR Team, hr@acme.com")
                f_signing_bonus = st.text_input("Signing Bonus", placeholder="e.g. $10,000 (optional)")

            f_benefits = st.text_area(
                "Benefits & Perks",
                placeholder="e.g. Health insurance, 20 days PTO, stock options, education budget…",
                height=68,
            )
            f_conditions = st.text_area(
                "Special Conditions",
                placeholder="e.g. 3-month probation, relocation package…",
                height=68,
            )
            f_extra = st.text_area(
                "Additional Instructions",
                placeholder="Any extra instructions for the AI (tone, format, etc.)",
                height=68,
            )

            submitted = st.form_submit_button("🚀 Generate Offer", use_container_width=True)

            if submitted:
                if not f_job_title.strip():
                    st.error("Job Title is required.")
                else:
                    # Build a structured prompt from form data
                    parts = [f"Generate a complete, professional job offer for the position of **{f_job_title.strip()}**."]
                    details = []
                    if f_candidate.strip():
                        details.append(f"Candidate name: {f_candidate.strip()}")
                    if f_email.strip():
                        details.append(f"Candidate email: {f_email.strip()}")
                    if f_salary.strip():
                        details.append(f"Base salary: {f_salary.strip()}")
                    if f_location.strip():
                        details.append(f"Location / work-mode: {f_location.strip()}")
                    if f_start_date.strip():
                        details.append(f"Start date: {f_start_date.strip()}")
                    if f_manager.strip():
                        details.append(f"Reporting manager: {f_manager.strip()}")
                    if f_company.strip():
                        details.append(f"Company: {f_company.strip()}")
                    if f_signing_bonus.strip():
                        details.append(f"Signing bonus: {f_signing_bonus.strip()}")
                    if f_contact.strip():
                        details.append(f"HR contact for signature: {f_contact.strip()}")
                    if f_benefits.strip():
                        details.append(f"Benefits & perks: {f_benefits.strip()}")
                    if f_conditions.strip():
                        details.append(f"Special conditions: {f_conditions.strip()}")

                    if details:
                        parts.append("\nDetails:\n- " + "\n- ".join(details))
                    if f_extra.strip():
                        parts.append(f"\nAdditional instructions: {f_extra.strip()}")

                    parts.append("\nPlease retrieve the best template, fill it, validate it, check market salary, and output the final offer letter.")

                    prompt = "\n".join(parts)
                    st.session_state.show_offer_form = False
                    _send_message(prompt)

st.divider()

# ── Chat history ───────────────────────────────────────────────
for message in st.session_state.messages:
    role = "user" if isinstance(message, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(message.content)

# ── Chat input ─────────────────────────────────────────────────
if user_input := st.chat_input("Message…"):
    _send_message(user_input)