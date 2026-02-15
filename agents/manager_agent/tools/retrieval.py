"""
Template Retrieval Tools

This module contains tools for retrieving HR templates
using RAG (Retrieval-Augmented Generation) with ChromaDB.

Group: Hiring Manager Agent (Group 2)

Tools:
- find_template: Query ChromaDB for best template by role
- ingest_templates_to_chromadb: Load templates into ChromaDB
"""

from typing import Optional, List
from langchain_core.tools import tool


try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


# ============================================================
# MOCK / BUILT-IN TEMPLATES
# ============================================================

MOCK_TEMPLATES = {
    "software": """
JOB OFFER: Software Engineer
Title: {{position}}
Salary: ${{salary}}
Location: {{location}}
Contract: {{contract}}

Benefits: Health, Dental, 401k
Description: We are looking for a skilled developer to join our engineering team.

Responsibilities:
- Design and develop scalable software solutions
- Collaborate with cross-functional teams
- Participate in code reviews and technical discussions
""",
    "sales": """
JOB OFFER: Sales Representative
Title: {{position}}
Salary: ${{salary}} + Commission
Location: {{location}}
Contract: {{contract}}

Benefits: Health, Travel allowance
Description: Join our dynamic sales team and help drive revenue growth.

Responsibilities:
- Build and maintain client relationships
- Meet quarterly sales targets
- Conduct product demonstrations
""",
    "management": """
JOB OFFER: Manager
Title: {{position}}
Salary: ${{salary}}
Location: {{location}}
Contract: {{contract}}

Benefits: Full package + Stock options
Description: Lead our team to success in a fast-paced environment.

Responsibilities:
- Manage and mentor a team of professionals
- Set strategic goals and track performance
- Collaborate with leadership on key initiatives
""",
    "intern": """
JOB OFFER: Internship
Title: {{position}}
Salary: ${{salary}} (stipend)
Location: {{location}}
Contract: {{contract}}

Benefits: Mentorship, Lunch allowance, Learning budget
Description: Kick-start your career with hands-on experience.

Responsibilities:
- Support the team with daily tasks
- Learn company tools and processes
- Present a final project at the end of the internship
""",
}

# ============================================================
# CHROMADB HELPERS
# ============================================================

_chroma_client = None
_chroma_collection = None


def get_chroma_client():
    """Get or create a singleton ChromaDB client."""
    global _chroma_client
    if not CHROMA_AVAILABLE:
        return None
    if _chroma_client is None:
        _chroma_client = chromadb.Client()  # In-memory for demo
    return _chroma_client


def initialize_chromadb_collection(collection_name: str = "hr_templates"):
    """
    Initialize (or retrieve) a ChromaDB collection and seed it with default
    templates if empty.

    Args:
        collection_name: Name of the ChromaDB collection.

    Returns:
        The ChromaDB collection object, or None if ChromaDB is unavailable.
    """
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection

    client = get_chroma_client()
    if not client:
        return None

    _chroma_collection = client.get_or_create_collection(name=collection_name)

    # Seed with mock templates if the collection is empty
    if _chroma_collection.count() == 0:
        ids = list(MOCK_TEMPLATES.keys())
        documents = list(MOCK_TEMPLATES.values())
        metadatas = [{"role": k, "type": "offer_template"} for k in ids]
        _chroma_collection.add(documents=documents, metadatas=metadatas, ids=ids)

    return _chroma_collection


# ============================================================
# NON-TOOL HELPERS
# ============================================================

def get_template(role_type: str, context: Optional[str] = None) -> dict:
    """
    Core template retrieval function (non-tool version).

    Args:
        role_type: Type of template to retrieve.
        context: Optional semantic context.

    Returns:
        Retrieved template data dictionary.
    """
    return find_template.invoke({"role_type": role_type, "context": context})


def list_available_templates() -> List[str]:
    """
    List all available template type IDs.

    Returns:
        List of template IDs / role names.
    """
    collection = initialize_chromadb_collection()
    if collection:
        try:
            result = collection.get()
            return result.get("ids", list(MOCK_TEMPLATES.keys()))
        except Exception:
            pass
    return list(MOCK_TEMPLATES.keys())


def add_template(
    template_type: str,
    name: str,
    content: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Add a single new template to ChromaDB.

    Args:
        template_type: Category of template (e.g. 'offer', 'email').
        name: Template name / ID.
        content: Template content.
        metadata: Additional metadata.

    Returns:
        Result dictionary.
    """
    collection = initialize_chromadb_collection()
    if not collection:
        # Fallback: just store in MOCK_TEMPLATES dict
        MOCK_TEMPLATES[name] = content
        return {"success": True, "storage": "in-memory fallback"}

    meta = {"role": template_type, "type": template_type}
    if metadata:
        meta.update(metadata)

    try:
        collection.add(documents=[content], metadatas=[meta], ids=[name])
        return {"success": True, "id": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# TOOLS
# ============================================================

@tool
def find_template(
    role_type: str,
    context: Optional[str] = None,
) -> dict:
    """
    Retrieve the best HR template based on role type.

    Queries ChromaDB (if available) or falls back to built-in templates.

    Args:
        role_type: Type of role/template to retrieve
                   (e.g., 'senior_engineer', 'sales', 'intern').
        context: Optional additional context for semantic matching.

    Returns:
        A dictionary with the template content and metadata.
    """
    try:
        # Attempt ChromaDB retrieval
        collection = initialize_chromadb_collection()
        if collection and collection.count() > 0:
            query_text = f"{role_type} {context or ''}"
            results = collection.query(query_texts=[query_text], n_results=1)

            if results["documents"] and results["documents"][0]:
                return {
                    "success": True,
                    "template": results["documents"][0][0],
                    "template_name": results["ids"][0][0],
                    "similarity_score": 0.9,
                    "alternatives": list_available_templates(),
                }

        # Fallback to built-in templates
        key = _resolve_template_key(role_type)
        return {
            "success": True,
            "template": MOCK_TEMPLATES[key],
            "template_name": key,
            "similarity_score": 1.0,
            "alternatives": list(MOCK_TEMPLATES.keys()),
        }

    except Exception as e:
        # Hard fallback
        key = _resolve_template_key(role_type)
        return {
            "success": True,
            "template": MOCK_TEMPLATES[key],
            "template_name": key,
            "similarity_score": 0.5,
            "alternatives": [],
            "warning": f"ChromaDB error, used fallback: {e}",
        }


@tool
def ingest_templates_to_chromadb(templates: list) -> dict:
    """
    Ingest a list of HR templates into ChromaDB.

    Args:
        templates: List of dicts, each with 'id', 'text', and optional 'metadata'.

    Returns:
        Status dictionary.
    """
    if not CHROMA_AVAILABLE:
        return {"success": False, "error": "ChromaDB not available"}

    try:
        collection = initialize_chromadb_collection()
        if not collection:
            return {"success": False, "error": "Failed to init collection"}

        ids = [t.get("id", str(i)) for i, t in enumerate(templates)]
        documents = [t.get("text", "") for t in templates]
        metadatas = [t.get("metadata", {}) for t in templates]

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return {"success": True, "count": len(ids)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# PRIVATE HELPERS
# ============================================================

def _resolve_template_key(role_type: str) -> str:
    """Resolve a role_type string to the best matching MOCK_TEMPLATES key."""
    role_lower = role_type.lower()
    if any(kw in role_lower for kw in ("engineer", "developer", "software", "tech")):
        return "software"
    if "sales" in role_lower:
        return "sales"
    if any(kw in role_lower for kw in ("manager", "director", "lead", "management")):
        return "management"
    if "intern" in role_lower:
        return "intern"
    return "software"
