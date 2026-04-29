from __future__ import annotations

from pathlib import Path

DEFAULT_PDF_NAME = (
    "CLI Paper-Research Landscape of Agentic AI and LLM - Apps, Challenges and Future Direction.pdf"
)

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_INDEX_PATH = DATA_DIR / "paper_index.json"


def resolve_default_pdf_path() -> Path:
    """Resolve the bundled paper path from the data directory."""
    data_pdf = DATA_DIR / DEFAULT_PDF_NAME
    if data_pdf.exists():
        return data_pdf

    data_pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if data_pdfs:
        return data_pdfs[0]

    raise FileNotFoundError("No PDF file was found in the data directory.")
