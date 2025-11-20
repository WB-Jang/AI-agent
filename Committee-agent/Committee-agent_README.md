```markdown
# Committee-agent — PDF → Text → LLM Summaries

This module provides a simple pipeline to:

1. Load PDF files from a directory
2. Extract text and break into overlapping character-based chunks
3. Summarize each chunk with an LLM (via LangChain)
4. Aggregate chunk summaries into a final summary

Key features:
- Default chunk size: 1000 characters
- Default overlap: 300 characters
- chunk_size and overlap are configurable as function arguments and CLI flags

Files:
- pdf_loader.py: extraction and chunking logic
- llm_summarizer.py: LangChain-based summarization (per-chunk + aggregation)
- run_pipeline.py: Example runnable script

Installation (example):
- Create a virtualenv and install:
  pip install -r requirements.txt

Example usage:
- From the repo root:
  python Committee-agent/run_pipeline.py /path/to/pdf_folder --chunk-size 1000 --overlap 300 --verbose

Change chunk_size / overlap:
- You can pass `chunk_size` and `overlap` either to:
  - pdf_loader.load_and_chunk_pdfs(dir_path, chunk_size=..., overlap=...)
  - the CLI flags (--chunk-size, --overlap)

LangChain LLM:
- By default the code uses ChatOpenAI from LangChain. You can pass any other LangChain LLM instance into summarize_chunks.
- Set your OpenAI key in the environment: `export OPENAI_API_KEY="..."`

LangGraph integration:
- This repo contains a basic, runnable LangChain pipeline. If you want to orchestrate the same steps within LangGraph,
  wrap `pdf_loader.load_and_chunk_pdfs` and `llm_summarizer.summarize_chunks` as nodes in a LangGraph graph.
- See `langgraph_integration.md` for guidance and a sample adapter stub.

Notes:
- Text extraction quality depends on the PDFs (scanned images require OCR; this loader does not perform OCR).
- If you need OCR, run PDFs through an OCR step (Tesseract / OCRmyPDF) before using this loader.
```