
import pytest
from src import agent


class FakeResponse:
    content = "Mock investigation report for automated testing."


class FakeLLM:
    def invoke(self, prompt):
        return FakeResponse()


def run_with_mocked_llm(monkeypatch, transaction_id):
    # Replace the entire LLM object instead of patching
    # the invoke method on the Pydantic model.
    monkeypatch.setattr(
        agent,
        "llm",
        FakeLLM()
    )

    return agent.investigate_payment(transaction_id)


@pytest.mark.parametrize(
    "transaction_id, expected_review",
    [
        ("TXN-10025", True),   # UPI timeout, 2 retries
        ("TXN-10026", False),  # Insufficient funds, 1 retry
        ("TXN-10027", False),  # Successful payment
        ("TXN-10028", True),   # Gateway timeout
        ("TXN-10029", True),   # Bank declined, 3 retries
    ]
)
def test_human_review_assessment(
    monkeypatch,
    transaction_id,
    expected_review
):
    result = run_with_mocked_llm(monkeypatch, transaction_id)

    assert result["transaction"] is not None
    assert result["requires_human_review"] == expected_review


def test_unknown_transaction():
    result = agent.investigate_payment("TXN-99999")

    assert result.get("transaction") is None
    assert "No transaction found" in result.get("error", "")


def test_rag_retrieves_matching_failure_knowledge(monkeypatch):
    result = run_with_mocked_llm(monkeypatch, "TXN-10025")

    knowledge = result.get("knowledge", [])

    assert len(knowledge) > 0

    for item in knowledge:
        assert item["failure_code"] == "UPI_TIMEOUT"

    assert any(
        "UPI_TIMEOUT" in item["section"]
        for item in knowledge
    )


def test_successful_transaction_skips_knowledge_retrieval(monkeypatch):
    result = run_with_mocked_llm(monkeypatch, "TXN-10027")

    assert result["transaction"]["status"] == "SUCCESS"
    assert result.get("knowledge", []) == []
