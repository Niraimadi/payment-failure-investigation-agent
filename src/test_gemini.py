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