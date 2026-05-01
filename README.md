# LLM CLI for Academic Paper Analysis

This project is a uv-managed Python CLI that answers questions about the supplied academic paper using a local Ollama model. It indexes the paper, retrieves the most relevant excerpts for each question, and asks the model to answer from those excerpts only.This is a lightweight single-document RAG system.

- It ingests a source document.
- It splits and indexes that document into chunks.
- For each question, it retrieves relevant chunks first.
- It sends those retrieved chunks to the - LLM as context for generation.
- That is the core RAG pattern: retrieval augmented generation.

- Project implements a lightweight, single-document RAG pipeline over one academic PDF. The core idea is simple: first retrieve the most relevant paper excerpts, then ask the local Ollama model to answer using only those excerpts. That control flow is driven from cli.py:111.


- (Term Frequency-Inverse Document Frequency) for its search and ranking.
- Tokenize the Question: First, it breaks your question down into a set of unique,
-  important keywords (tokens). It converts the question to lowercase and removes common "stopwords" (like "a", "the", "is") that don't add much meaning.
- Calculate TF-IDF Scores: For each keyword from your question, it calculates a TF-IDF (Term Frequency-Inverse Document Frequency) score against every chunk in the paper.
- Term Frequency (TF): How often does the keyword appear in a specific chunk? (More appearances = higher score).
- Inverse Document Frequency (IDF): How rare is the keyword across all chunks? (Rarer words like "agentic" are given more weight than common words like "system").
- Score Each Chunk: The total relevance score for a chunk is the sum of the TF-IDF scores of all the question's keywords found within that chunk.
- Rank and Select: The chunks are then ranked from highest score to lowest. The system retrieves the top_k chunks (your default is 4).


## Features

- Accepts questions from the command line.
- Indexes the supplied academic paper into searchable chunks.
- Retrieves supporting excerpts before generating an answer.
- Uses a local Ollama model such as `llama3`.
- Refuses to answer when the paper evidence is insufficient.

* Ollama is the local model runtime and API server. It is the software that downloads models, starts a local inference service, and lets your CLI send prompts to that service. llama3 is the actual large language model. More precisely, it is the model family your app asks Ollama to run.

So in this project, the full flow is:

1. The user asks a question in the CLI
2. The code retrieves relevant paper chunks
3. those chunks are sent to Ollama
4. Ollama runs llama3
5. llama3 returns the answer

## Current Project Structure

```text
.
├── .dockerignore
├── .python-version
├── compose.yaml
├── Dockerfile
├── README.md
├── app.py
├── data/
│   ├── CLI Paper-Research Landscape of Agentic AI and LLM - Apps, Challenges and Future Direction.pdf
│   └── paper_index.json
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

- `pyproject.toml`: package metadata, dependencies, pytest settings, and Ruff configuration(Ruff is the Python code-quality linting tool).
- `uv.lock`: locked dependency graph for reproducible environments.
- `Dockerfile`: production-oriented container image for the CLI.
- `compose.yaml`: local multi-container setup for the CLI plus Ollama.
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

## Docker

Build the CLI image:

```bash
docker build -t paper-qa-cli .
```

Check the containerized CLI entrypoint:

```bash
docker run --rm paper-qa-cli --help
```

Run the container against an Ollama server already running on your host machine:

```bash
docker run --rm \
	-e OLLAMA_URL=http://host.docker.internal:11434/api/generate \
	paper-qa-cli ask "What differences does the paper identify between LLM systems and agentic AI systems?"
```

Use Compose when you want Docker to run Ollama for you as well:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3
docker compose run --rm paper-qa ask "What differences does the paper identify between LLM systems and agentic AI systems?"
```

Open an interactive chat session through Compose:

```bash
docker compose run --rm paper-qa chat
```

Stop the Ollama service when you are done:

```bash
docker compose down
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

- Keep the PDF under `data/`, or
- pass the file explicitly with `--paper`.

## Production Preparedness

The repository has been updated to production standards:

- Continuous Integration (CI) configuration file exists for testing and lint testing before deployments (`.github/workflows/ci.yml`).
- A basic `Dockerfile` exposes a straightforward, easily reproducible CLI environment. (e.g. `docker build -t paper-cli .` followed by `docker run --rm paper-cli --help`).
- Standardised Logging has been implemented with `logging` allowing to customize the log messages via `-v` / `--verbose` command line parameter substituting typical terminal stack traces with informative, well formatted output.

# Runbook

1. In the first terminal:

```bash
  ollama serve
```

2. In the second terminal:

```bash
uv run paper-qa build-index

```

3. Then ask these five questions:

```bash
uv run paper-qa ask "What differences does the paper identify between LLM systems and agentic AI systems?"
```

```bash
uv run paper-qa ask "How does the paper describe the role of tools or external actions in agentic systems?"
```

```bash
uv run paper-qa ask "What challenges or limitations are highlighted for agentic AI systems?"
```

```bash
uv run paper-qa ask "What future research directions does the paper suggest?"
```

```bash
uv run paper-qa ask "Which capabilities are emphasized for LLM systems compared with agentic systems?"
```

4. Then ask one unsupported question to show the system refuses to use outside knowledge:

```bash
uv run paper-qa ask "What does the paper say about marine biology field sampling?"
```

Expected outcome: the CLI should refuse because the paper does not cover that topic.

5. Dry-run

```bash
uv run paper-qa ask "What differences does the paper identify between LLM systems and agentic AI systems?" --dry-run

```

### Why Dry-run matters:

- it proves retrieval happens before answer generation
- it shows exactly what evidence the system found in the paper
- it helps to explain grounding very clearly in class

## Cloud Deployment Demo (Google Cloud)

This section outlines how to run the complete project on a cloud VM, demonstrating real-world deployment trade-offs between model size and hardware constraints. This setup uses a standard `e2-standard-2` VM on Google Cloud.

### 1. Initial VM Setup

Connect to your cloud VM and ensure the environment is ready.

```bash
# Connect to your VM instance
gcloud compute ssh your-instance-name --zone your-zone

# Clone the repository for the first time
git clone https://github.com/caglagezgen/LLM-CLI-ForAcademicPaperAnalysis.git
cd LLM-CLI-ForAcademicPaperAnalysis

# Ensure Docker service is running
sudo systemctl start docker
```

### 2. Start Services and Prepare Models

Start the Ollama service in the background and download the models we will compare.

```bash
# Start the Ollama service in detached mode
sudo docker-compose up -d ollama


# Pull the small, fast model for low-resource environments(Current VM's has memory limit so we will use a smaller model)
sudo docker-compose exec ollama ollama pull tinyllama
```

Current VM's has memory limit so we will use a smaller model

```bash
# Run the same question with the small model
sudo docker-compose run paper-qa ask --model tinyllama "What differences does the paper identify between LLM systems and agentic AI systems?"
```
- Then ask these five questions:

```bash
sudo docker-compose run paper-qa ask --model tinyllama "What differences does the paper identify between LLM systems and agentic AI systems?"
```

```bash
sudo docker-compose run paper-qa ask --model tinyllama "How does the paper describe the role of tools or external actions in agentic systems?"
```

```bash
sudo docker-compose run paper-qa ask --model tinyllama  "What challenges or limitations are highlighted for agentic AI systems?"
```

```bash
sudo docker-compose run paper-qa ask --model tinyllama  "What future research directions does the paper suggest?"
```

```bash
sudo docker-compose run paper-qa ask --model tinyllama  "Which capabilities are emphasized for LLM systems compared with agentic systems?"
```
```bash
sudo docker-compose run paper-qa ask --model tinyllama  "What is meant by multi agent systems"
```

- Then ask one unsupported question to show the system refuses to use outside knowledge:

```bash
sudo docker-compose run paper-qa ask --model tinyllama  "What does the paper say about marine biology field sampling?"
```


```bash
# Ask a question that is not in the paper
sudo docker-compose run paper-qa ask --model tinyllama "What does the paper say about marine biology?"
```
