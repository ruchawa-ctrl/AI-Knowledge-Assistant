from io import BytesIO

from pypdf import PdfReader


def extract_text(filename: str, content_type: str, raw: bytes) -> str:
    """Extract plain text from an uploaded file (PDF or text-like)."""
    name = filename.lower()
    if name.endswith(".pdf") or content_type == "application/pdf":
        reader = PdfReader(BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()
    # Treat everything else as UTF-8 text (txt, md, csv, etc.)
    return raw.decode("utf-8", errors="ignore").strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping word-based chunks.

    Word-based windows keep chunks reasonably sized without needing a tokenizer
    at ingestion time, which keeps ingestion fast and dependency-light.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks
