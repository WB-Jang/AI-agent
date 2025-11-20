# Complete validation pipeline integrating pdf_loader, validator, and langgraph workflow

import argparse
import os
import json
from typing import Optional
from langchain.chat_models import ChatOpenAI
from pdf_loader import load_and_chunk_pdfs
from text_validator import TextValidator
from langgraph_validator import run_validation_workflow


def validate_pdfs_simple(
    dir_path: str,
    chunk_size: int = 1000,
    overlap: int = 300,
    llm: Optional[ChatOpenAI] = None,
    verbose: bool = False,
) -> Dict:
    """
    Simple pipeline: Load PDFs -> Chunk -> Validate (without LangGraph).

    Useful for quick validation without workflow orchestration.
    """
    if not os.path.isdir(dir_path):
        raise ValueError(f"{dir_path} is not a valid directory")

    # Load and chunk PDFs
    chunks = load_and_chunk_pdfs(
        dir_path, chunk_size=chunk_size, overlap=overlap, include_filenames=True
    )
    if verbose:
        print(f"✓ Loaded and chunked {len(chunks)} chunks from {dir_path}")

    # Initialize validator
    llm = llm or ChatOpenAI(temperature=0, model="gpt-4")
    validator = TextValidator(llm=llm)

    # Validate all chunks
    results = validator.validate_all_chunks(chunks, verbose=verbose)

    return results


def validate_pdfs_with_graph(
    dir_path: str,
    chunk_size: int = 1000,
    overlap: int = 300,
    llm: Optional[ChatOpenAI] = None,
    verbose: bool = False,
) -> Dict:
    """
    Advanced pipeline: Load PDFs -> Chunk -> Validate via LangGraph workflow.

    Uses LangGraph for orchestration and allows for more complex routing logic.
    """
    if not os.path.isdir(dir_path):
        raise ValueError(f"{dir_path} is not a valid directory")

    # Load and chunk PDFs
    chunks = load_and_chunk_pdfs(
        dir_path, chunk_size=chunk_size, overlap=overlap, include_filenames=True
    )
    if verbose:
        print(f"✓ Loaded and chunked {len(chunks)} chunks from {dir_path}")

    # Initialize LLM
    llm = llm or ChatOpenAI(temperature=0, model="gpt-4")

    # Run validation workflow via LangGraph
    result = run_validation_workflow(chunks, llm=llm, verbose=verbose)

    return result


def format_validation_report(result: Dict) -> str:
    """Format validation results into a readable report"""
    report = []
    report.append("=" * 60)
    report.append("📋 텍스트 검증 보고서")
    report.append("=" * 60)

    # Summary
    summary = result.get("summary", {})
    report.append("\n📊 요약:")
    report.append(f"  • 전체 청크: {summary.get('total_chunks', 0)}")
    report.append(f"  • 정상 청크: {summary.get('clean_chunks', 0)}")
    report.append(f"  • 경고 청크: {summary.get('warning_chunks', 0)}")
    report.append(f"  • 심각 오류 청크: {summary.get('critical_chunks', 0)}")
    report.append(f"  • 품질 점수: {summary.get('overall_quality_score', 0.0)} / 1.0")

    # Aggregate findings
    report.append("\n🔍 통합 분석:")
    aggregate = result.get("aggregate_findings", "분석 결과 없음")
    report.append(aggregate[:500] + "..." if len(aggregate) > 500 else aggregate)

    # Problematic chunks
    chunk_validations = result.get("chunk_validations", [])
    problematic = [v for v in chunk_validations if v["severity"] != "clean"]

    if problematic:
        report.append(f"\n⚠️  문제가 있는 청크 (총 {len(problematic)}개):")
        for i, chunk_val in enumerate(problematic[:5]):  # Show first 5
            report.append(f"\n  [{i + 1}] 청크 {chunk_val['chunk_index']} ({chunk_val['source']})")
            report.append(f"      심각도: {chunk_val['severity'].upper()}")
            if chunk_val.get("typo_validation", {}).get("has_typos"):
                report.append("      오타 발견:")
                findings = chunk_val["typo_validation"]["typo_findings"][:200]
                report.append(f"      {findings}...")

    report.append("\n" + "=" * 60)
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Validate PDFs for typos and logical errors")
    parser.add_argument("pdf_dir", help="Directory containing PDF files")
    parser.add_argument(
        "--chunk-size", type=int, default=1000, help="Chunk size in characters"
    )
    parser.add_argument("--overlap", type=int, default=300, help="Overlap size in characters")
    parser.add_argument(
        "--mode",
        choices=["simple", "graph"],
        default="simple",
        help="Validation mode: simple (LangChain) or graph (LangGraph)",
    )
    parser.add_argument("--output", help="Save report to JSON file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not os.path.isdir(args.pdf_dir):
        print(f"❌ Error: {args.pdf_dir} is not a valid directory")
        return

    # Run validation
    print(f"🚀 Starting PDF validation in {args.mode} mode...")
    llm = ChatOpenAI(temperature=0, model="gpt-4")

    if args.mode == "simple":
        result = validate_pdfs_simple(
            args.pdf_dir,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            llm=llm,
            verbose=args.verbose,
        )
    else:  # graph
        result = validate_pdfs_with_graph(
            args.pdf_dir,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            llm=llm,
            verbose=args.verbose,
        )

    # Format and display report
    report = format_validation_report(result)
    print(report)

    # Save to file if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Report saved to {args.output}")


if __name__ == "__main__":
    main()