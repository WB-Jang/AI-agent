# PDF loader and chunker for Committee-agent
# - Extracts text from PDFs in a directory
# - Produces overlapping character-based chunks
# - chunk_size and overlap are configurable per-call

import os
from typing import List, Dict, Iterable
from pypdf import PdfReader


def extract_text_from_pdf(path: str) -> str:
    """
    Extracts text from all pages of a PDF file using pypdf.
    Returns a single concatenated string with simple page separators.
    """
    reader = PdfReader(path)
    texts = []
    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            # Fallback: ignore page extraction errors and continue
            page_text = ""
        texts.append(page_text)
    # join with a page separator to preserve page boundaries for metadata if needed
    return "\n\n[PAGE_BREAK]\n\n".join(texts)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 300) -> Iterable[Dict]:
    """
    Break `text` into chunks of `chunk_size` characters with `overlap` characters overlap.
    Yields dicts containing:
      - "text": chunk text
      - "start": start char index (inclusive)
      - "end": end char index (exclusive)
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text_length = len(text)
    start = 0
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        yield {"text": chunk, "start": start, "end": min(end, text_length)}
        # advance start by chunk_size - overlap
        start += chunk_size - overlap


def load_and_chunk_pdfs(
    dir_path: str,
    chunk_size: int = 1000,
    overlap: int = 300,
    include_filenames: bool = True,
) -> List[Dict]:
    """
    Load all PDF files from `dir_path`, extract text and chunk into overlapping pieces.

    Returns a list of chunk dicts:
      {
        "text": str,
        "metadata": {
          "source": "<filename.pdf>",
          "chunk_index": int,
          "start": int,
          "end": int
        }
      }

    - chunk_size and overlap are configurable per-call.
    - Only files ending with .pdf (case-insensitive) are processed.
    """
    results = []
    filenames = sorted(
        [
            f
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
            and f.lower().endswith(".pdf")
        ]
    )

    for filename in filenames:
        full_path = os.path.join(dir_path, filename)
        text = extract_text_from_pdf(full_path)
        if not text.strip():
            # skip empty extraction
            continue
        for idx, chunk_meta in enumerate(chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
            metadata = {"chunk_index": idx, "start": chunk_meta["start"], "end": chunk_meta["end"]}
            if include_filenames:
                metadata["source"] = filename
            results.append({"text": chunk_meta["text"], "metadata": metadata})
    return results