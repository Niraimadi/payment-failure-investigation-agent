
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing!")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,
    temperature=0.2,
    max_retries=3,
    timeout=60
)

print(f"LLM initialized with model: {MODEL_NAME}")
