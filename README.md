# LLM CLI for Academic Paper Analysis

This project is a uv-managed Python CLI that answers questions about the supplied academic paper using a local Ollama model. It indexes the paper, retrieves the most relevant excerpts for each question, and asks the model to answer from those excerpts only.This is a lightweight single-document RAG system.

- It ingests a source document.
- It splits and indexes that document into chunks.
- For each question, it retrieves relevant chunks first.
- It sends those retrieved chunks to the - LLM as context for generation.
- That is the core RAG pattern: retrieval augmented generation.



## Features

- Accepts questions from the command line.
- Indexes the supplied academic paper into searchable chunks.
- Retrieves supporting excerpts before generating an answer.
- Uses a local Ollama model such as `llama3`.
- Refuses to answer when the paper evidence is insufficient.

## Current Project Structure

```text
.
├── .python-version
├── README.md
├── app.py
├── CLI Paper-Research Landscape of Agentic AI and LLM - Apps, Challenges and Future Direction.pdf
├── data/
│   └── paper_index.json
├── projectRequirements.md
├── pyproject.toml
├── src/
│   └── paper_qa_cli/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── ollama_client.py
│       ├── paper_index.py
│       └── paths.py
├── tests/
│   └── test_paper_index.py
└── uv.lock
```

## Key Files

- `pyproject.toml`: package metadata, dependencies, pytest settings, and Ruff configuration.
- `uv.lock`: locked dependency graph for reproducible environments.
- `src/paper_qa_cli/cli.py`: main CLI entrypoint and command definitions.
- `src/paper_qa_cli/paper_index.py`: PDF extraction, chunking, indexing, and retrieval.
- `src/paper_qa_cli/ollama_client.py`: Ollama integration and grounded prompting.
- `src/paper_qa_cli/paths.py`: default paths for the paper and generated index.
- `tests/test_paper_index.py`: retrieval and refusal behavior tests.
- `app.py`: compatibility wrapper around the packaged CLI.

## Prerequisites

- Python 3.11
- `uv`
- Ollama installed locally
- A local Ollama model such as `llama3`

## Setup

Install `uv` on macOS if needed:

```bash
brew install uv
```

Create and sync the environment from `pyproject.toml` and `uv.lock`:

```bash
uv sync
```

Pull the default Ollama model:

```bash
ollama pull llama3
```

Start the Ollama service:

```bash
ollama serve
```

## Run The Project

Show CLI help:

```bash
uv run paper-qa --help
```

Build the cached paper index:

```bash
uv run paper-qa build-index
```

Ask a single question:

```bash
uv run paper-qa ask "What differences does the paper identify between LLM systems and agentic AI systems?"
```

Inspect retrieval without calling Ollama:

```bash
uv run paper-qa ask "What challenges are discussed in the paper?" --dry-run
```

Start an interactive session:

```bash
uv run paper-qa chat
```

Use a specific paper file explicitly:

```bash
uv run paper-qa ask --paper /path/to/paper.pdf "What future directions does the paper suggest?"
```

Force the index to rebuild before answering:

```bash
uv run paper-qa ask --rebuild "What differences does the paper identify between LLM systems and agentic AI systems?"
```

## Alternative Entry Points

These commands also work from the project root:

```bash
uv run python -m paper_qa_cli chat
uv run python app.py chat
```

## Test And Lint

Run the test suite:

```bash
uv run pytest
```

Run lint checks:

```bash
uv run ruff check .
```

Auto-fix simple Ruff issues:

```bash
uv run ruff check --fix .
```

## Grounding Behavior

The CLI first retrieves the most relevant chunks from the indexed paper and only passes those excerpts to Ollama. If the retrieved evidence is not strong enough, the CLI returns a refusal instead of inventing an answer.

The `--dry-run` option is useful for demonstrations because it shows the retrieved evidence without depending on the LLM response.

## Example Questions

- What differences does the paper identify between LLM systems and agentic AI systems?
- What challenges or limitations are highlighted for agentic AI systems?
- How does the paper describe the role of tools or external actions in agentic systems?
- What future research directions does the paper suggest?
- Which capabilities are emphasized for LLM systems compared with agentic systems?

## Troubleshooting

If `uv run paper-qa ask ...` fails with an Ollama connection error:

- Confirm Ollama is installed.
- Confirm the service is running with `ollama serve`.
- Confirm the model exists with `ollama list`.

If the CLI cannot find the paper automatically:

- Keep the PDF in the project root, or
- place it under `data/`, or
- pass the file explicitly with `--paper`.
## Production Preparedness

The repository has been updated to production standards:
- Continuous Integration (CI) configuration file exists for testing and lint testing before deployments (`.github/workflows/ci.yml`).
- A basic `Dockerfile` exposes a straightforward, easily reproducible CLI environment. (e.g. `docker build -t paper-cli .` followed by `docker run --rm paper-cli --help`).
- Standardised Logging has been implemented with `logging` allowing to customize the log messages via `-v` / `--verbose` command line parameter substituting typical terminal stack traces with informative, well formatted output.

