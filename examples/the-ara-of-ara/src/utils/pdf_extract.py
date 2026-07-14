"""PDF text extraction using PyMuPDF + vision-based markdown conversion."""

import base64
import hashlib
import re
from pathlib import Path

import anthropic
import pymupdf


def extract_text(pdf_path: str) -> str:
    """Extract and clean text from a PDF file (lightweight fallback).

    Returns the full text with normalized whitespace,
    stripped headers/footers, and cleaned encoding artifacts.
    """
    doc = pymupdf.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        # Strip common header/footer patterns (page numbers, running titles)
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            stripped = line.strip()
            # Skip isolated page numbers
            if re.match(r"^\d{1,3}$", stripped):
                continue
            # Skip very short lines that look like running headers
            if len(stripped) < 3 and stripped not in ("", "-"):
                continue
            cleaned.append(line)
        pages.append("\n".join(cleaned))
    full_text = "\n\n".join(pages)
    # Normalize whitespace: collapse multiple blank lines
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    # Fix common PDF artifacts
    full_text = full_text.replace("\u2019", "'")
    full_text = full_text.replace("\u2018", "'")
    full_text = full_text.replace("\u201c", '"')
    full_text = full_text.replace("\u201d", '"')
    full_text = full_text.replace("\ufb01", "fi")
    full_text = full_text.replace("\ufb02", "fl")
    full_text = full_text.replace("\u2013", "--")
    full_text = full_text.replace("\u2014", "---")
    return full_text.strip()


_MD_CONVERSION_PROMPT = (
    "Convert this research paper PDF into a faithful, complete markdown document. "
    "Preserve ALL content — do not summarize or skip sections.\n\n"
    "Requirements:\n"
    "1. Section headings with proper hierarchy (# for title, ## for sections, "
    "### for subsections)\n"
    "2. ALL tables as markdown tables with exact cell values — no rounding, "
    "no omission. Include table number and caption above each table.\n"
    "3. Math notation as LaTeX: $inline$ and $$display$$\n"
    "4. Figure captions labeled as **Figure N**: {caption}\n"
    "5. Algorithm pseudocode in fenced code blocks with line numbers\n"
    "6. All citations inline as [Author et al., Year] or [N]\n"
    "7. Footnotes and appendix content included\n\n"
    "Output ONLY the markdown. Do NOT add commentary or meta-text."
)


def _pdf_hash(pdf_path: str) -> str:
    """Compute a fast content hash for a PDF file."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        # Hash first 64KB + file size for fast fingerprinting
        chunk = f.read(65536)
        h.update(chunk)
        f.seek(0, 2)
        h.update(str(f.tell()).encode())
    return h.hexdigest()[:16]


def extract_markdown(
    pdf_path: str,
    cache_dir: str | None = None,
    model: str = "claude-sonnet-4-6",
) -> str:
    """Convert PDF to high-quality markdown using Claude's PDF vision.

    Caches result to disk keyed by PDF content hash so the same PDF
    is never re-processed. Preserves tables, headings, math, and captions.

    Args:
        pdf_path: Path to the PDF file.
        cache_dir: Directory for caching results. Defaults to code/.cache/pdf_md/.
        model: Model to use for conversion.

    Returns:
        Markdown string of the full paper.
    """
    # Resolve cache directory
    if cache_dir is None:
        cache_dir = str(Path(__file__).resolve().parent.parent / ".cache" / "pdf_md")
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    # Check cache
    content_hash = _pdf_hash(pdf_path)
    cached_file = cache_path / f"{content_hash}.md"
    if cached_file.is_file():
        print(f"[pdf_extract] Cache hit: {cached_file}")
        return cached_file.read_text()

    # Convert PDF to markdown via Claude vision
    print(f"[pdf_extract] Converting PDF to markdown (model={model})...")
    pdf_bytes = open(pdf_path, "rb").read()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=model,
        max_tokens=64_000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": _MD_CONVERSION_PROMPT},
                ],
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    markdown = "".join(b.text for b in response.content if hasattr(b, "text"))

    # Cache result
    cached_file.write_text(markdown)
    print(
        f"[pdf_extract] Converted {len(pdf_bytes)} bytes PDF -> "
        f"{len(markdown)} chars markdown (cached: {cached_file})"
    )

    return markdown


def extract_tables_vision(pdf_path: str) -> str:
    """Extract all tables from a PDF using Claude's vision capabilities.

    NOTE: Prefer extract_markdown() which does a full conversion including
    tables. This function is kept for backward compatibility and for cases
    where only tables are needed.
    """
    pdf_bytes = open(pdf_path, "rb").read()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")

    client = anthropic.Anthropic()
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16_000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract ALL tables from this PDF as markdown. "
                            "For each table:\n"
                            "1. State the table number/label and caption\n"
                            "2. Reproduce the table as a markdown table with exact "
                            "column headers and every cell value copied precisely "
                            "(no rounding, no omission)\n"
                            "3. Note the section where the table appears\n\n"
                            "Output ONLY the markdown tables, no commentary."
                        ),
                    },
                ],
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    return "".join(b.text for b in response.content if hasattr(b, "text"))
