# indexing and retrieval logic

from __future__ import annotations

import json
import re
import types
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
COMPARISON_TERMS = (
    "difference",
    "differences",
    "compare",
    "compared",
    "comparison",
    "contrast",
    "whereas",
    "while",
)
CONCEPT_ALIASES = {
    "llm": ("llm", "llms", "large language model", "large language models"),
    "agentic": ("agentic", "agentic ai", "agentic system", "agentic systems", "agent"),
    "tool": ("tool", "tools", "tool use", "external tools"),
    "reason": ("reason", "reasoning", "reasoning capabilities"),
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "what",
    "when",
    "which",
    "with",
}


@dataclass(slots=True)
class Chunk:
    """Represents a chunk extracted from the PDF."""
    chunk_id: int
    page_number: int
    text: str


@dataclass(slots=True)
class SearchHit:
    """A text chunk alongside its relevance score."""
    chunk: Chunk
    score: float


@dataclass(slots=True)
class PaperIndex:
    """JSON serializable wrapper storing the paper's chunks."""
    pdf_path: str
    chunk_size: int
    chunks: list[Chunk]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a basic dictionary."""
        return {
            "pdf_path": self.pdf_path,
            "chunk_size": self.chunk_size,
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PaperIndex:
        """Deserialize from basic dictionary."""
        raw_chunks = payload.get("chunks", [])
        chunks = [Chunk(**raw_chunk) for raw_chunk in raw_chunks]
        return cls(
            pdf_path=str(payload.get("pdf_path", "")),
            chunk_size=int(payload.get("chunk_size", 0)),
            chunks=chunks,
        )


def build_index(pdf_path: Path, index_path: Path, chunk_size: int = 1200) -> PaperIndex:
    """Builds and serializes a lexical index over the given PDF file."""
    pdf_module = _require_pypdf()
    reader = pdf_module.PdfReader(str(pdf_path))
    chunks: list[Chunk] = []
    chunk_id = 1

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = _normalize_text(page.extract_text() or "")
        if not page_text:
            continue

        for chunk_text in _chunk_text(page_text, chunk_size):
            chunks.append(Chunk(chunk_id=chunk_id, page_number=page_number, text=chunk_text))
            chunk_id += 1

    if not chunks:
        raise RuntimeError("No text could be extracted from the PDF.")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    paper_index = PaperIndex(pdf_path=str(pdf_path), chunk_size=chunk_size, chunks=chunks)
    index_path.write_text(
        json.dumps(paper_index.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return paper_index


def load_index(index_path: Path) -> PaperIndex:
    """Loads a previously saved PaperIndex from disk."""
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    return PaperIndex.from_dict(payload)


def search_index(question: str, paper_index: PaperIndex, top_k: int = 4) -> list[SearchHit]:
    """Find the top_k most relevant chunks using a lexical scoring heuristic."""
    question_terms = _tokenize(question)
    if not question_terms:
        return []

    question_lower = question.lower()
    concept_groups = _detect_query_concepts(question_lower, question_terms)
    comparison_query = any(term in question_lower for term in COMPARISON_TERMS)

    hits: list[SearchHit] = []
    for chunk in paper_index.chunks:
        score = _score_chunk(
            question_terms=question_terms,
            question_lower=question_lower,
            chunk_text=chunk.text,
            concept_groups=concept_groups,
            comparison_query=comparison_query,
        )
        if score > 0:
            hits.append(SearchHit(chunk=chunk, score=score))

    hits.sort(key=lambda hit: (hit.score, len(hit.chunk.text)), reverse=True)
    return hits[:top_k]


def summarize_hit(hit: SearchHit, limit: int = 280) -> str:
    """Truncates the search hit text explicitly if necessary."""
    excerpt = hit.chunk.text
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 3].rstrip() + "..."
    return (
        f"chunk {hit.chunk.chunk_id} | page {hit.chunk.page_number} | "
        f"score {hit.score:.2f}\n{excerpt}"
    )


def _require_pypdf() -> types.ModuleType:
    """Dynamically loads pypdf to handle PDFs."""
    try:
        import pypdf
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency 'pypdf'. Install the project dependencies first."
        ) from exc
    return pypdf


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\u00a0", " ")
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _chunk_text(text: str, chunk_size: int) -> list[str]:
    sentences = [sentence.strip() for sentence in SENTENCE_PATTERN.split(text) if sentence.strip()]
    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_length = 0

    for sentence in sentences:
        if len(sentence) >= chunk_size:
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_length = 0
            chunks.extend(_split_long_sentence(sentence, chunk_size))
            continue

        projected_length = current_length + len(sentence) + (1 if current_sentences else 0)
        if current_sentences and projected_length > chunk_size:
            chunks.append(" ".join(current_sentences))
            current_sentences = [current_sentences[-1], sentence]
            current_length = len(current_sentences[0]) + len(sentence) + 1
            continue

        current_sentences.append(sentence)
        current_length = projected_length

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def _split_long_sentence(sentence: str, chunk_size: int) -> list[str]:
    words = sentence.split()
    pieces: list[str] = []
    current_words: list[str] = []
    current_length = 0

    for word in words:
        projected_length = current_length + len(word) + (1 if current_words else 0)
        if current_words and projected_length > chunk_size:
            pieces.append(" ".join(current_words))
            current_words = [word]
            current_length = len(word)
            continue

        current_words.append(word)
        current_length = projected_length

    if current_words:
        pieces.append(" ".join(current_words))

    return pieces


def _tokenize(text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def _detect_query_concepts(question_lower: str, question_terms: list[str]) -> list[tuple[str, ...]]:
    concepts: list[tuple[str, ...]] = []
    joined_terms = " ".join(question_terms)

    for aliases in CONCEPT_ALIASES.values():
        if any(alias in question_lower or alias in joined_terms for alias in aliases):
            concepts.append(aliases)

    return concepts


def _score_chunk(
    question_terms: list[str],
    question_lower: str,
    chunk_text: str,
    concept_groups: list[tuple[str, ...]],
    comparison_query: bool,
) -> float:
    chunk_terms = _tokenize(chunk_text)
    if not chunk_terms:
        return 0.0

    chunk_lower = chunk_text.lower()
    frequencies = Counter(chunk_terms)
    overlap_terms = {term for term in question_terms if term in frequencies}
    if not overlap_terms:
        return 0.0

    overlap_score = len(overlap_terms) * 2.0
    frequency_score = sum(frequencies[term] for term in question_terms) * 0.4
    phrase_bonus = 1.5 if " ".join(question_terms) in chunk_lower else 0.0

    concept_bonus = 0.0
    matched_concepts = 0
    for aliases in concept_groups:
        if any(alias in chunk_lower for alias in aliases):
            matched_concepts += 1
            concept_bonus += 2.5
    if concept_groups and matched_concepts == len(concept_groups):
        concept_bonus += 3.0

    comparison_bonus = 0.0
    if comparison_query and any(term in chunk_lower for term in COMPARISON_TERMS):
        comparison_bonus = 1.5

    exact_question_bonus = 1.0 if question_lower in chunk_lower else 0.0
    return (
        overlap_score
        + frequency_score
        + phrase_bonus
        + concept_bonus
        + comparison_bonus
        + exact_question_bonus
    )