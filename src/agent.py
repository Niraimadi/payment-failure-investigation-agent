
import json
from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END

from src.database import get_transaction
from src.retriever import retrieve_knowledge
from src.llm import llm


class InvestigationState(TypedDict, total=False):
    transaction_id: str
    transaction: dict[str, Any] | None
    knowledge: list[dict[str, Any]]
    report: str
    error: str
    requires_human_review: bool
    review_reason: str


# Node 1: Retrieve transaction from SQLite
def retrieve_transaction(state: InvestigationState):

    transaction_id = state["transaction_id"]

    print(f"\nRetrieving transaction: {transaction_id}")

    transaction = get_transaction(transaction_id)

    return {
        "transaction": transaction
    }


# Node 2: Retrieve relevant troubleshooting knowledge
def retrieve_payment_knowledge(state: InvestigationState):

    transaction = state["transaction"]

    print("\nRetrieving payment troubleshooting knowledge...")

    failure_code = transaction.get("failure_code")

    # Successful transactions or transactions without a failure code
    # do not need failure-code-specific retrieval.
    if not failure_code:
        print("No failure code available. Skipping knowledge retrieval.")

        return {
            "knowledge": []
        }

    query = (
        f"Troubleshooting guidance for payment failure code "
        f"{failure_code}. Explain possible causes, investigation "
        f"steps and recommended actions."
    )

    documents = retrieve_knowledge(
        query=query,
        k=3,
        failure_code=failure_code
    )

    knowledge = []

    for document in documents:

        knowledge.append({
            "failure_code": document.metadata.get("failure_code"),
            "section": document.metadata.get("section"),
            "content": document.page_content,
            "source": document.metadata.get("source")
        })

    print(f"Retrieved {len(knowledge)} relevant knowledge sections.")

    return {
        "knowledge": knowledge
    }


def assess_human_review(state: InvestigationState):
    transaction = state["transaction"]

    status = transaction["status"]
    failure_code = transaction.get("failure_code")
    retry_count = transaction.get("retry_count", 0)

    requires_review = False
    reason = ""

    if status == "PENDING":
        requires_review = True
        reason = "Transaction is still pending. Verify its final status."

    elif failure_code in ["UPI_TIMEOUT", "GATEWAY_TIMEOUT"]:
        requires_review = True
        reason = (
            "Payment timeout detected. Verify the original "
            "transaction status with the payment provider."
        )

    elif status == "FAILED" and retry_count >= 2:
        requires_review = True
        reason = (
            "Multiple payment attempts detected. "
            "Manual verification is recommended."
        )

    print("\nAssessing human review requirement...")
    print(f"Manual review required: {requires_review}")

    return {
        "requires_human_review": requires_review,
        "review_reason": reason
    }


# Node 3: Analyse transaction and retrieved knowledge using Gemini
def analyse_transaction(state: InvestigationState):

    transaction = state["transaction"]
    knowledge = state.get("knowledge", [])

    print("\nAnalysing transaction using Gemini with RAG context...")

    transaction_json = json.dumps(
        transaction,
        indent=2
    )

    knowledge_context = "\n\n".join(
        [
            f"Source: {item['source']}\n"
            f"Section: {item['section']}\n"
            f"Content:\n{item['content']}"
            for item in knowledge
        ]
    )

    if not knowledge_context:
        knowledge_context = (
            "No failure-specific troubleshooting knowledge "
            "was retrieved for this transaction."
        )

    prompt = f"""
You are a payment failure investigation assistant.

Investigate the transaction using the transaction data
and the retrieved payment troubleshooting knowledge.

TRANSACTION DATA:
{transaction_json}

RETRIEVED KNOWLEDGE:
{knowledge_context}

Instructions:

1. Explain the current transaction status.
2. Identify the failure reason, if applicable.
3. Explain possible causes based on the transaction data
   and retrieved knowledge.
4. Recommend appropriate investigation steps.
5. Mention whether human intervention is required.
6. Clearly distinguish verified facts from possible causes.
7. If no relevant knowledge was retrieved, mention this
   rather than inventing troubleshooting guidance.
8. Do not invent transaction details.
9. Do not claim to have initiated a refund, retry or
   any other payment operation.

Structure the report using these sections:

- Transaction Summary
- Failure Analysis
- Possible Causes
- Recommended Investigation Steps
- Recommended Actions
- Human Intervention

Provide a clear and concise investigation report.
"""

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, str):
        report = content
    elif isinstance(content, list):
        report = "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        report = str(content)

    return {"report": report}


# Node 4: Handle missing transactions
def transaction_not_found(state: InvestigationState):

    transaction_id = state["transaction_id"]

    return {
        "error": f"No transaction found for {transaction_id}",
        "report": (
            "Investigation could not proceed because "
            "the transaction ID does not exist."
        ),
        "knowledge": []
    }


# Conditional routing after transaction retrieval
def route_after_retrieval(state: InvestigationState):

    if state.get("transaction"):
        return "retrieve_knowledge"

    return "not_found"


# Build LangGraph workflow
builder = StateGraph(InvestigationState)

builder.add_node("retrieve", retrieve_transaction)
builder.add_node("retrieve_knowledge", retrieve_payment_knowledge)
builder.add_node("analyse", analyse_transaction)
builder.add_node("not_found", transaction_not_found)
builder.add_node("assess_review", assess_human_review)

builder.add_edge(START, "retrieve")

builder.add_conditional_edges(
    "retrieve",
    route_after_retrieval,
    {
        "retrieve_knowledge": "retrieve_knowledge",
        "not_found": "not_found"
    }
)

builder.add_edge("retrieve_knowledge", "assess_review")
builder.add_edge("assess_review", "analyse")

builder.add_edge("analyse", END)
builder.add_edge("not_found", END)

payment_agent = builder.compile()


def investigate_payment(transaction_id: str):

    initial_state = {
        "transaction_id": transaction_id
    }

    result = payment_agent.invoke(initial_state)

    return result


if __name__ == "__main__":

    transaction_id = input("Enter transaction ID: ").strip()

    if not transaction_id:
        print("Please enter a valid transaction ID.")

    else:

        result = investigate_payment(transaction_id)

        print("\n========== INVESTIGATION REPORT ==========")

        print(result["report"])

        print("\n========== RETRIEVED KNOWLEDGE ==========")

        for item in result.get("knowledge", []):
            print(f"\nFailure code: {item['failure_code']}")
            print(f"Section: {item['section']}")
            print(item["content"])

        print("\n==========================================")
