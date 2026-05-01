# Ollama integration
# This template gives the model very specific instructions on how to behave.
from __future__ import annotations

import json
import logging
import os
from urllib import error, request

from .paper_index import SearchHit

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_URL = os.environ.get("OLLAMA_URL", os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_URL))
# This template gives the model very specific instructions on how to behave.
REFUSAL_TEXT = "The paper does not provide enough information to answer that question."
SYSTEM_PROMPT = (
    "You answer questions about a single academic paper. Use only the provided paper excerpts. "
    "Do not use outside knowledge, assumptions, or speculation. If the excerpts do not contain "
    f"enough evidence, reply with exactly: '{REFUSAL_TEXT}' "
    "Then list the excerpts that support your answer."
)

logger = logging.getLogger(__name__)


class OllamaError(RuntimeError):
    """Exception raised for errors during Ollama API communication."""

    pass


def answer_question(
    question: str,
    hits: list[SearchHit],
    model: str,
    ollama_url: str = OLLAMA_URL,
) -> str:
    """Answers a question using the local Ollama API based on retrieved chunks.

    Args:
        question: The user's query.
        hits: A list of SearchHit objects representing relevant chunks retrieved from the paper.
        model: The name of the local Ollama model to use.
        ollama_url: The API endpoint URL for the Ollama generate endpoint.

    Returns:
        The generated answer string from the model, or a refusal if evidence is insufficient.

    Raises:
        OllamaError: If the API request fails or returns an error.
    """
    if not hits:
        logger.debug("No search hits provided, returning refusal.")
        return REFUSAL_TEXT

    context = _format_context(hits)
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": (
            "Answer the question using only the paper excerpts below.\n\n"
            f"Question: {question}\n\n"
            "Return the answer in this format:\n"
            "Answer: <short answer>\n"
            "Evidence: <chunk ids and short justification>\n\n"
            f"Paper excerpts:\n{context}"
        ),
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }

    logger.debug("Sending request to Ollama endpoint: %s with model: %s", ollama_url, model)
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        ollama_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=300) as response:
            raw_payload = response.read().decode("utf-8")
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        logger.error("HTTP error from Ollama: %s", message)
        raise OllamaError(f"Ollama request failed: {message}") from exc
    except error.URLError as exc:
        logger.error("URL error, could not reach Ollama at %s", ollama_url)
        raise OllamaError(
            f"Could not reach Ollama. Ensure the local Ollama service is listening on {ollama_url}."
        ) from exc

    response_payload = json.loads(raw_payload)
    if response_payload.get("error"):
        logger.error("Ollama API returned an error: %s", response_payload.get("error"))
        raise OllamaError(str(response_payload["error"]))

    answer = str(response_payload.get("response", "")).strip()
    return answer or REFUSAL_TEXT


def _format_context(hits: list[SearchHit]) -> str:
    """Formats the retrieved search hits into a prompt-friendly string."""
    parts = []
    for hit in hits:
        parts.append(
            f"[chunk {hit.chunk.chunk_id} | page {hit.chunk.page_number}]\n{hit.chunk.text}"
        )
    return "\n\n".join(parts)
