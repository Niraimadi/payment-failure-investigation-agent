
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = (
    BASE_DIR / "knowledge_base" / "payment_troubleshooting.md"
)

VECTOR_DB_PATH = BASE_DIR / "data" / "chroma_db"


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def load_documents():
    """Load and split knowledge base by Markdown sections."""

    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError("Knowledge base file not found.")

    content = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")

    sections = re.split(
        r"(?=^## )",
        content,
        flags=re.MULTILINE
    )

    documents = []

    for section in sections:

        section = section.strip()

        if not section.startswith("## "):
            continue

        title = section.splitlines()[0].replace("## ", "").strip()

        code_match = re.search(r"\b[A-Z_]{3,}\b", title)

        failure_code = code_match.group(0) if code_match else "GENERAL"

        documents.append(
            Document(
                page_content=section,
                metadata={
                    "source": "payment_troubleshooting.md",
                    "section": title,
                    "failure_code": failure_code
                }
            )
        )

    print(f"Loaded {len(documents)} knowledge sections.")

    return documents


def get_vector_store():

    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

    # v2 uses section-based documents instead of character-based chunks.
    vector_store = Chroma(
        collection_name="payment_knowledge_v2",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DB_PATH)
    )

    if vector_store._collection.count() == 0:

        print("Creating embeddings for knowledge sections...")

        documents = load_documents()

        vector_store.add_documents(documents)

        print("Knowledge base indexed successfully!")

    else:
        print("Existing section-based vector database loaded.")

    return vector_store


def retrieve_knowledge(
    query: str,
    k: int = 3,
    failure_code: str | None = None
):
    """Retrieve relevant knowledge, optionally filtering by failure code."""

    vector_store = get_vector_store()

    search_filter = None

    if failure_code:
        search_filter = {
            "failure_code": failure_code
        }

    results = vector_store.similarity_search(
        query=query,
        k=k,
        filter=search_filter
    )

    return results


if __name__ == "__main__":

    search_query = (
        "UPI payment failed because the bank server did not respond"
    )

    results = retrieve_knowledge(search_query)

    print("\n========== RETRIEVED KNOWLEDGE ==========")

    for index, document in enumerate(results, start=1):

        print(f"\nResult {index}:")
        print("Failure code:", document.metadata["failure_code"])
        print("Section:", document.metadata["section"])
        print(document.page_content)

    print("\n=========================================")
