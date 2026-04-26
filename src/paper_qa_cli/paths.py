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
    """Resolve local paper path robustly from the repository root."""
    project_pdf = PROJECT_ROOT / DEFAULT_PDF_NAME
    if project_pdf.exists():
        return project_pdf

    data_pdf = DATA_DIR / DEFAULT_PDF_NAME
    if data_pdf.exists():
        return data_pdf

    pdf_files = sorted(PROJECT_ROOT.glob("*.pdf"))
    if pdf_files:
        return pdf_files[0]

    data_pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if data_pdfs:
        return data_pdfs[0]

    raise FileNotFoundError("No PDF file was found in the project directory.")