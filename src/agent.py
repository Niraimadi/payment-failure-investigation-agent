
import json
from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END

from src.database import get_transaction
from src.llm import llm


# 1. Define the shared graph state
class InvestigationState(TypedDict, total=False):
    transaction_id: str
    transaction: dict[str, Any] | None
    report: str
    error: str


# 2. Node: Retrieve transaction from SQLite
def retrieve_transaction(state: InvestigationState):

    transaction_id = state["transaction_id"]

    print(f"\nRetrieving transaction: {transaction_id}")

    transaction = get_transaction(transaction_id)

    return {
        "transaction": transaction
    }


# 3. Node: Analyse transaction using Gemini
def analyse_transaction(state: InvestigationState):

    transaction = state["transaction"]

    print("\nAnalysing transaction using Gemini...")

    transaction_json = json.dumps(
        transaction,
        indent=2
    )

    prompt = f"""
    You are a payment failure investigation assistant.

    Analyse the following transaction details.

    TRANSACTION DATA:
    {transaction_json}

    Instructions:

    1. Explain the transaction status.
    2. Identify the failure reason, if applicable.
    3. Explain the possible cause based only on the
       provided evidence.
    4. Recommend appropriate next investigation steps.
    5. Mention whether human intervention is required.

    Important:
    - Do not invent transaction details.
    - Do not assume a payment was successful or failed
      without checking its status.
    - Distinguish confirmed facts from possible causes.
    - Never claim that you have initiated a refund,
      retry or other payment operation.

    Format the response as a clear investigation report.
    """

    response = llm.invoke(prompt)

    return {
        "report": str(response.content)
    }


# 4. Node: Handle transaction not found
def transaction_not_found(state: InvestigationState):

    transaction_id = state["transaction_id"]

    return {
        "error": f"No transaction found for {transaction_id}",
        "report": (
            "Investigation could not proceed because "
            "the transaction ID does not exist."
        )
    }


# 5. Conditional routing function
def route_after_retrieval(state: InvestigationState):

    if state.get("transaction"):
        return "analyse"

    return "not_found"


# 6. Build the LangGraph workflow
builder = StateGraph(InvestigationState)

builder.add_node(
    "retrieve",
    retrieve_transaction
)

builder.add_node(
    "analyse",
    analyse_transaction
)

builder.add_node(
    "not_found",
    transaction_not_found
)

# Define graph entry point
builder.add_edge(START, "retrieve")

# Define conditional routing
builder.add_conditional_edges(
    "retrieve",
    route_after_retrieval,
    {
        "analyse": "analyse",
        "not_found": "not_found"
    }
)

# Define ending edges
builder.add_edge("analyse", END)
builder.add_edge("not_found", END)

# Compile graph
payment_agent = builder.compile()


# 7. Execute the agent
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
        try:
            result = investigate_payment(transaction_id)

            print("\n========== INVESTIGATION REPORT ==========")
            print(result["report"])
            print("==========================================")

        except Exception as e:
            print(f"\nInvestigation failed: {e}")