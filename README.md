## 🤖 Intelligent HR Recruitment Agent


📌 This repository is a personal mirror of a team project originally developed by ATIA Club ESB (7 contributors). 

A next-generation, agentic recruitment platform built around a conversational chat interface that manages the entire hiring workflow — from analyzing CVs to generating job offers.

## 🎯 Our Goal

The objective is to move beyond simple, static dashboards and create a dynamic, conversational AI partner for HR professionals. Instead of clicking buttons, the user will interact with an agent in natural language.

**User:** "Rank these 5 CVs for the Senior AI Engineer role."
**Agent:** "Done. Here is the ranked list. Candidate 2 (92%) and Candidate 5 (88%) are the strongest matches. Would you like me to generate a job offer for the top candidate?"

## ✨ Core Features (Agent Tools)

The agent's "brain" (built with LangGraph) will have access to a set of specialized tools, which our teams will build:

* **CV Parser (`cv_parser_tool`):** Extracts raw text from uploaded PDF and DOCX files.
* **Skill Extractor (`skill_extractor_tool`):** Uses a RAG pipeline (with FAISS) to read a CV's text and return a structured JSON of skills, experience, and education.
* **Similarity Matcher (`similarity_matcher_tool`):** Takes the extracted skills JSON and a job description, and calculates a semantic similarity score using Sentence Transformers.
* **Candidate Ranker (`cv_ranker_tool`):** A tool that can take a list of candidates and their scores (from the agent's memory) and return a sorted, ranked list.
* **Job Offer Generator (`job_offer_generator_tool`):** A separate RAG pipeline (with ChromaDB) that uses a knowledge base of company templates to generate a complete, personalized job offer.

## 🏗️ Architecture Overview

<img width="1272" height="528" alt="image" src="https://github.com/user-attachments/assets/0333a9fe-e7c8-4f0a-8b6c-97b3fa7f7735" />

This project is built on a modern, agentic architecture.

* **Frontend:** **Streamlit** (Single-page chat interface).
* **Backend (The "Brain"):** **LangGraph**. A central agent (in `agent.py`) maintains the "state" (memory) of the conversation and decides which tool to call next.
* **Tools:** The RAG pipelines and functions in `tools/` that the agent uses to perform tasks.
* **Databases:**
    * **FAISS:** A fast, in-memory vector store for on-the-fly CV skill extraction.
    * **ChromaDB:** A persistent vector store to act as the long-term memory/knowledge base for the Job Offer Generator.

## 🛠️ Technology Stack

* **Frontend:** Streamlit
* **Agent Logic:** LangGraph, LangChain
* **LLM:** Groq (Llama 3)
* **Embeddings:** Sentence Transformers
* **Vector Stores:** FAISS (CPU), ChromaDB
* **File Parsing:** PyPDF2, python-docx
* **CI/CD:** Docker, GitHub Actions

## 🚀 Getting Started (Local Setup)

This is the guide for all team members to get the project running locally.

### Prerequisites

* Python 3.10+
* Git

### 1. Clone the Repository

```bash
git clone https://github.com/Taher1412/intelligent-recruitment-platform.git
cd intelligent-recruitment-platform
```

### 2. Create a Virtual Environment

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up API Key

This project requires a Groq API key. We use Streamlit's built-in secrets management.

1. Create a folder: `.streamlit`
2. Inside that folder, create a file: `secrets.toml`
3. Add your key to that file:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "Your-Groq-API-Key-Goes-Here"
```

(This file is in .gitignore, so you will never accidentally commit your key).

### 5. Run the Application

```bash
streamlit run app.py
```

Open your browser to http://localhost:8501 to see the app.

## 📁 Project Structure

```
├── .streamlit/
│   └── secrets.toml        # (Local) API keys
├── tools/
│   ├── __init__.py
│   ├── cv_tools.py         # Squad 1 (CV, Match, Rank)
│   └── offer_tools.py      # Squad 2 (Job Offer Generator)
├── .gitignore
├── app.py                  # Main Streamlit UI
├── agent.py                # LangGraph "Brain" (Router & State)
├── requirements.txt
└── README.md               # This file
```

🤝 About This Project

This platform was built collaboratively by a 7-person team as part of ATIA Club ESB, following a structured workflow: task tracking on Trello, feature branches, and pull requests reviewed before merging into main.
