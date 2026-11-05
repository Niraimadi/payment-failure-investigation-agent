import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm import llm


def test_gemini():

    response = llm.invoke(
        "Explain what a failed UPI transaction means "
        "in simple terms. Keep it within 3 sentences."
    )

    print("\nGemini response:")
    print(response.content)


if __name__ == "__main__":
    test_gemini()