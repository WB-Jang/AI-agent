# Example runnable pipeline that ties pdf_loader and llm_summarizer together.
# Update OPENAI_API_KEY or provide a different LLM instance if needed.
#
# Usage:
#   python Committee-agent/run_pipeline.py /path/to/pdf_dir --chunk-size 1000 --overlap 300

import argparse
import os
from committee_agent import pdf_loader, llm_summarizer
from langchain.chat_models import ChatOpenAI


def main():
    parser = argparse.ArgumentParser(description="Load PDFs, chunk, and summarize using LangChain.")
    parser.add_argument("pdf_dir", help="Directory containing PDF files")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=300, help="Overlap size in characters")
    parser.add_argument("--openai-temperature", type=float, default=0.0, help="LLM temperature")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not os.path.isdir(args.pdf_dir):
        raise SystemExit(f"{args.pdf_dir} is not a directory")

    # Load & chunk PDFs
    chunks = pdf_loader.load_and_chunk_pdfs(args.pdf_dir, chunk_size=args.chunk_size, overlap=args.overlap)
    if args.verbose:
        print(f"Loaded {len(chunks)} chunks from PDFs in {args.pdf_dir}")

    # Instantiate LLM (ChatOpenAI by default)
    llm = ChatOpenAI(temperature=args.openai_temperature)

    # Summarize
    result = llm_summarizer.summarize_chunks(chunks, llm=llm, verbose=args.verbose)

    print("=== FINAL SUMMARY ===")
    print(result["final_summary"])
    print("\n=== PER-CHUNK SUMMARIES (first 5) ===")
    for item in result["chunk_summaries"][:5]:
        print(item["metadata"].get("source", "?"), item["metadata"].get("chunk_index", "?"))
        print(item["summary"])
        print("---")


if __name__ == "__main__":
    main()