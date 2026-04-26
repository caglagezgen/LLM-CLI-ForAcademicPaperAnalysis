# real CLI entry point

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .ollama_client import REFUSAL_TEXT, OllamaError, answer_question
from .paper_index import (
    PaperIndex,
    SearchHit,
    build_index,
    load_index,
    search_index,
    summarize_hit,
)
from .paths import DEFAULT_INDEX_PATH, resolve_default_pdf_path

DEFAULT_MODEL = "llama3"
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool) -> None:
    """Configures the root logger based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    
    setup_logging(getattr(args, "verbose", False))

    try:
        if args.command == "build-index":
            pdf_path = _resolve_pdf_path(args.paper)
            paper_index = build_index(pdf_path, args.index, chunk_size=args.chunk_size)
            print(f"Indexed {len(paper_index.chunks)} chunks from {pdf_path.name} into {args.index}.")
            return 0

        if args.command == "ask":
            return _ask_once(args)

        if args.command == "chat":
            return _chat_loop(args)

        parser.print_help()
        return 1
    except (OllamaError, RuntimeError, FileNotFoundError) as exc:
        logger.error("Error: %s", exc)
        return 1


def _ask_once(args: argparse.Namespace) -> int:
    pdf_path = _resolve_pdf_path(args.paper)
    paper_index = _ensure_index(pdf_path, args.index, args.chunk_size, args.rebuild)
    result = _run_question(
        question=args.question,
        paper_index=paper_index,
        model=args.model,
        top_k=args.top_k,
        min_score=args.min_score,
        dry_run=args.dry_run,
    )
    print(result)
    return 0


def _chat_loop(args: argparse.Namespace) -> int:
    pdf_path = _resolve_pdf_path(args.paper)
    paper_index = _ensure_index(pdf_path, args.index, args.chunk_size, args.rebuild)

    print("Paper-grounded CLI is ready. Type 'exit' to quit.")
    while True:
        try:
            question = input("\nQuestion: ").strip()
        except EOFError:
            print()
            return 0

        if question.lower() in {"exit", "quit"}:
            return 0
        if not question:
            continue

        try:
            print(
                _run_question(
                    question=question,
                    paper_index=paper_index,
                    model=args.model,
                    top_k=args.top_k,
                    min_score=args.min_score,
                    dry_run=False,
                )
            )
        except OllamaError as exc:
            logger.error("Error: %s", exc)
            return 1


def _run_question(
    question: str,
    paper_index: PaperIndex,
    model: str,
    top_k: int,
    min_score: float,
    dry_run: bool,
) -> str:
    hits = search_index(question, paper_index, top_k=top_k)
    filtered_hits = [hit for hit in hits if hit.score >= min_score]

    if not filtered_hits:
        return f"Answer:\n{REFUSAL_TEXT}\n\nRetrieved excerpts:\nNone"

    if dry_run:
        answer = "Dry run enabled. No Ollama response generated."
    else:
        answer = answer_question(question=question, hits=filtered_hits, model=model)

    return _format_output(answer, filtered_hits)


def _format_output(answer: str, hits: list[SearchHit]) -> str:
    evidence_lines = "\n\n".join(summarize_hit(hit) for hit in hits)
    return f"Answer:\n{answer}\n\nRetrieved excerpts:\n{evidence_lines}"


def _ensure_index(
    pdf_path: Path,
    index_path: Path,
    chunk_size: int,
    rebuild: bool,
) -> PaperIndex:
    if rebuild or not index_path.exists():
        return build_index(pdf_path, index_path, chunk_size=chunk_size)
    return load_index(index_path)


def _resolve_pdf_path(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        if not explicit_path.exists():
            raise FileNotFoundError(f"PDF not found: {explicit_path}")
        return explicit_path
    return resolve_default_pdf_path()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask paper-grounded questions about the provided academic paper."
    )
    subparsers = parser.add_subparsers(dest="command")

    common_parent = argparse.ArgumentParser(add_help=False)
    common_parent.add_argument(
        "--paper",
        type=Path,
        default=None,
        help="Path to the source PDF. Defaults to the bundled paper.",
    )
    common_parent.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Path to the cached JSON index.",
    )
    common_parent.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Approximate chunk size used during indexing.",
    )

    common_parent.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging.",
    )
    qa_parent = argparse.ArgumentParser(add_help=False, parents=[common_parent])
    qa_parent.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Ollama model name to use for answering.",
    )
    qa_parent.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of supporting chunks to retrieve.",
    )
    qa_parent.add_argument(
        "--min-score",
        type=float,
        default=2.0,
        help="Minimum retrieval score required before asking the model.",
    )
    qa_parent.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the JSON index before answering.",
    )

    build_parser = subparsers.add_parser(
        "build-index",
        parents=[common_parent],
        help="Extract the PDF and cache it into a JSON index.",
    )
    build_parser.set_defaults(command="build-index")

    ask_parser = subparsers.add_parser(
        "ask",
        parents=[qa_parent],
        help="Ask a single question about the paper.",
    )
    ask_parser.add_argument("question", help="The question to ask about the paper.")
    ask_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip Ollama and only print the retrieved paper excerpts.",
    )
    ask_parser.set_defaults(command="ask")

    chat_parser = subparsers.add_parser(
        "chat",
        parents=[qa_parent],
        help="Open an interactive CLI session.",
    )
    chat_parser.set_defaults(command="chat")

    return parser