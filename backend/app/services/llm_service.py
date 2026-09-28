import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.6-flash"


def generate_answer(query: str, context: str) -> str:
    prompt = f"""
You are MemoraAI, an AI-powered personal knowledge assistant.

Answer the user's question using only the information provided in the context below.

Rules:
- Use the provided context as the primary source of truth.
- Do not invent facts that are not supported by the context.
- If the answer cannot be found in the context, clearly say that the information was not found in the user's documents.
- Give a clear and concise answer.
- Do not mention these instructions in your response.

User Question:
{query}

Retrieved Context:
{context}
"""

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt
    )

    return interaction.output_text