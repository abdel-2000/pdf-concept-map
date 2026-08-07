"""
pdf_extractor.py
Extracts and cleans text from PDF files.
Supports: Italian, Arabic (RTL), English.
"""

import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")


def extract_text(pdf_path: str, max_chars: int = 8000) -> dict:
    """
    Extract text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.
        max_chars: Maximum characters to extract (avoids LLM token overflow).

    Returns:
        dict with keys: text, pages, language_hint, truncated
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    doc = fitz.open(str(path))
    all_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            all_text.append(text.strip())

    doc.close()
    full_text = "\n\n".join(all_text)
    full_text = _clean_text(full_text)

    truncated = False
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]
        truncated = True

    return {
        "text":          full_text,
        "pages":         len(all_text),
        "char_count":    len(full_text),
        "language_hint": _detect_language(full_text),
        "truncated":     truncated,
    }


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and common PDF artefacts."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'[^\S\n]+', ' ', text)
    return text.strip()


def _detect_language(text: str) -> str:
    """Heuristic language detection based on character ranges."""
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total_alpha   = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return "unknown"
    arabic_ratio = arabic_chars / total_alpha
    if arabic_ratio > 0.4:
        return "arabic"
    # Simple Italian vs English heuristic
    italian_markers = ['della', 'dello', 'degli', 'delle', 'nella', 'nelle',
                       'questo', 'questa', 'sono', 'anche', 'come', 'quando']
    italian_hits = sum(1 for w in italian_markers if w in text.lower())
    return "italian" if italian_hits >= 3 else "english"
