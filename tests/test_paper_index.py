from __future__ import annotations

from paper_qa_cli.cli import _run_question
from paper_qa_cli.ollama_client import REFUSAL_TEXT
from paper_qa_cli.paper_index import Chunk, PaperIndex, search_index


def test_comparison_query_prefers_comparison_chunk() -> None:
    """Test that comparison terms elevate chunks that contain comparing language."""
    paper_index = PaperIndex(
        pdf_path="paper.pdf",
        chunk_size=500,
        chunks=[
            Chunk(
                chunk_id=1,
                page_number=1,
                text=(
                    "LLM systems focus on language understanding and reasoning capabilities, "
                    "whereas agentic AI systems pursue goals and interact with tools to take "
                    "actions."
                ),
            ),
            Chunk(
                chunk_id=2,
                page_number=2,
                text="This section surveys general advances in deep neural architectures.",
            ),
        ],
    )

    hits = search_index(
        "What are the differences between LLM systems and agentic AI systems?",
        paper_index,
        top_k=1,
    )

    assert len(hits) == 1
    assert hits[0].chunk.chunk_id == 1


def test_run_question_refuses_when_paper_has_no_support() -> None:
    """Ensure we explicitly refuse if the document does not provide context."""
    paper_index = PaperIndex(
        pdf_path="paper.pdf",
        chunk_size=500,
        chunks=[
            Chunk(
                chunk_id=1,
                page_number=1,
                text=(
                    "LLM systems focus on language understanding and reasoning capabilities, "
                    "whereas agentic AI systems pursue goals and interact with tools to take "
                    "actions."
                ),
            ),
        ],
    )

    result = _run_question(
        question="What does the paper say about marine biology field sampling?",
        paper_index=paper_index,
        model="llama3",
        top_k=4,
        min_score=2.0,
        dry_run=True,
    )

    assert REFUSAL_TEXT in result
    assert "Retrieved excerpts:\nNone" in result