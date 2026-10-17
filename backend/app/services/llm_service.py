
import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3").strip()


SYSTEM_PROMPT = """You are MemoraAI, an intelligent personal knowledge assistant.

Your task is to answer the user's question accurately using ONLY the information provided in the Document Context below.

Guidelines:

1. Grounding and Accuracy:
   - Base your answer strictly on facts supported by the Document Context.
   - Do NOT invent facts, unsupported explanations, calculations, or conclusions.
   - If the context does not contain enough information, clearly state:
     "The uploaded documents do not contain enough information to answer this question."
   - For calculations, use the values and methods provided in the context. Show intermediate steps when appropriate.

2. Formatting and Readability:
   - Use clean, structured Markdown.
   - Use **bold terms** for important concepts.
   - Use bullet points and numbered lists where appropriate.
   - Use clear headings (### Heading) for multi-part answers.
   - Keep answers organized, readable, and appropriate for a learner.

3. Mathematical Notation:
   - Write inline mathematical expressions using single dollar signs, for example: $n = p \\times q$.
   - Write standalone equations using double dollar signs on separate lines, for example:
     $$n = p \\times q$$
   - Do NOT wrap equations in ordinary parentheses as a substitute for math delimiters.
   - Use valid LaTeX commands such as \\times, \\phi, \\gcd, \\bmod, \\equiv, and \\pmod inside math delimiters.
   - Write powers clearly, for example: $C = M^e \\bmod n$.
   - Avoid malformed expressions such as $M^{,e}$.
   - For numerical problems, present the formula, substitute the given values, calculate the result, and briefly explain the step.
   - Ensure all math expressions have matching delimiters.

4. Tables:
   - Use standard GitHub-flavored Markdown tables when comparing items or organizing calculations.
   - Keep each cell concise and readable.
   - For mathematical expressions inside table cells, use inline math delimiters, for example, `$n = 3 \\times 11 = 33$`.
   - Do not put multiline display equations inside table cells.
   - Do not use a table when a short list would be clearer.

5. Sources:
   - Cite only documents that actually support the answer.
   - Do not include unrelated uploaded documents in the source list.
   - Do not claim a document supports a statement unless its content supports that statement.

6. Conversation History:
   - Use conversation history to understand follow-up questions and references to earlier topics.
   - Keep answers grounded in the uploaded documents.
   - Never reveal raw internal system details, chunk numbers, or internal chunk IDs.
"""


def _format_extractive_fallback(query: str, context: str) -> str:
    """Format an extractive structured answer from retrieved context if LLM API key is pending."""
    clean_lines = [
        line.strip()
        for line in context.split("\n")
        if line.strip() and not line.startswith("[Document:")
    ]

    query_words = set(w.lower() for w in query.split() if len(w) > 3)
    scored = []

    for line in clean_lines:
        if len(line) < 25:
            continue

        words = set(w.lower() for w in line.split())
        score = len(query_words.intersection(words))
        scored.append((score, line))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_lines = [item[1] for item in scored[:4]] or clean_lines[:3]

    bullets = []

    for line in top_lines:
        # Bold the first few words or key term for readability
        parts = line.split(" ", 4)

        if len(parts) >= 3:
            first_part = " ".join(parts[:2])
            rest = " ".join(parts[2:])
            bullets.append(f"- **{first_part}**: {rest}")
        else:
            bullets.append(f"- **Information**: {line}")

    bullets_text = "\n".join(bullets)

    return (
        f"### Knowledge Insights from Uploaded Documents\n\n"
        f"Based on your uploaded documents, here is the relevant grounded context:\n\n"
        f"{bullets_text}\n\n"
        f"> *Note: To enable generative AI synthesis and follow-ups, configure your free Groq key in `backend/.env` (`GROQ_API_KEY=...` from [console.groq.com](https://console.groq.com)).*"
    )


def _generate_with_groq(
    query: str,
    context: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Generate answer using Groq API."""
    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY).strip()

    if not api_key:
        return _format_extractive_fallback(query, context)

    try:
        from groq import Groq, RateLimitError, APIConnectionError, APIStatusError

        client = Groq(api_key=api_key)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        if chat_history:
            for msg in chat_history[-6:]:
                role = "assistant" if msg.get("sender") == "assistant" else "user"
                messages.append({
                    "role": role,
                    "content": msg.get("content", "")
                })

        user_content = f"Document Context:\n{context}\n\nUser Question:\n{query}"
        messages.append({
            "role": "user",
            "content": user_content
        })

        primary_model = os.getenv("GROQ_MODEL", GROQ_MODEL).strip()
        candidate_models = [
            primary_model,
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b"
        ]

        last_error = None

        for candidate in candidate_models:
            try:
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model=candidate,
                    temperature=0.2,
                    max_tokens=4096,
                )   

                
                choice = chat_completion.choices[0]
                answer = choice.message.content or ""

                logger.warning(
                    "Groq response: model=%s, finish_reason=%s, output_chars=%s",
                    candidate,
                    choice.finish_reason,
                    len(answer)
                )

                logger.warning("RAW GROQ ANSWER:\n%s", answer)

                return answer


            except APIStatusError as status_err:
                last_error = status_err

                if status_err.status_code == 404:
                    continue  # Try next candidate model

                raise

        if last_error:
            raise last_error

    except RateLimitError:
        logger.warning("Groq rate limit reached.")
        return (
            "**Notice: LLM Quota Limit Reached**\n\n"
            "The Groq API rate limit or quota has temporarily been reached. "
            "Please wait a moment before asking your next question."
        )

    except APIConnectionError as e:
        logger.error("Groq connection error: %s", e)
        return (
            "**Connection Error**\n\n"
            "Unable to connect to the Groq LLM service. Please check your internet connection."
        )

    except APIStatusError as e:
        logger.error("Groq API status error: %s", e)
        return (
            f"**Service Error:** The LLM provider returned an error "
            f"({e.status_code}). Please verify your model and API key configuration."
        )

    except Exception as e:
        logger.error("Unexpected Groq error: %s", e)
        return f"**Error generating answer:** {str(e)}"


def _generate_with_ollama(
    query: str,
    context: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Generate answer using local Ollama instance."""
    import httpx

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if chat_history:
        for msg in chat_history[-6:]:
            role = "assistant" if msg.get("sender") == "assistant" else "user"
            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

    user_content = f"Document Context:\n{context}\n\nUser Question:\n{query}"
    messages.append({
        "role": "user",
        "content": user_content
    })

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=60.0
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("message", {}).get("content", "")

        return (
            f"**Ollama Error:** Received status code {response.status_code}. "
            f"Please ensure model `{OLLAMA_MODEL}` is pulled (`ollama pull {OLLAMA_MODEL}`)."
        )

    except httpx.ConnectError:
        logger.warning("Could not connect to Ollama at %s", OLLAMA_BASE_URL)
        return (
            f"**Ollama Offline**\n\n"
            f"Could not connect to Ollama at `{OLLAMA_BASE_URL}`. "
            "Please ensure Ollama is installed and running locally, or switch "
            "`LLM_PROVIDER=groq` in `backend/.env`."
        )

    except Exception as e:
        logger.error("Ollama error: %s", e)
        return f"**Ollama Error:** {str(e)}"


def generate_answer(
    query: str,
    context: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Main entry point for generating answers.
    Routes to the configured provider (Groq or Ollama) and handles errors gracefully.
    """
    if not context or not context.strip():
        return (
            "The uploaded documents do not contain enough information to answer this question. "
            "Please upload relevant documents or rephrase your question."
        )

    provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()

    logger.warning("Configured LLM provider: %s", provider)

    if provider == "ollama":
        return _generate_with_ollama(query, context, chat_history)

    return _generate_with_groq(query, context, chat_history)

