# Example test cases for the text validator

import json
from langchain.chat_models import ChatOpenAI
from text_validator import TextValidator
from pdf_loader import load_and_chunk_pdfs
from validation_pipeline import validate_pdfs_simple, format_validation_report


def test_validator_with_sample_text():
    """Test the validator with sample Korean text"""
    
    sample_chunks = [
        {
            "text": "한국의 수도는 서울이다. 서울은 한반도의 중앙에 위치하고 있고, 약 1000만명의 인구를 가지고 있다.",
            "metadata": {"source": "test.pdf", "chunk_index": 0}
        },
        {
            "text": "파이썬은 프로그래밍 언어이며, 간단한 문법과 강력한 기능을 갖추고 있다. 그러나 C언어는 더 빠르다.",
            "metadata": {"source": "test.pdf", "chunk_index": 1}
        },
        {
            "text": "사과는 빨간색이다. 그런데 바나나는 노랑색이고, 동시에 빨간색이다. 이것은 모순이다.",
            "metadata": {"source": "test.pdf", "chunk_index": 2}
        },
        {
            "text": "오늘은 날씨가 좋습니다. 하지만 내일 비가온다고 했습니다. 우리는 우산을 들고가야 된다.",
            "metadata": {"source": "test.pdf", "chunk_index": 3}
        }
    ]

    llm = ChatOpenAI(temperature=0, model="gpt-4")
    validator = TextValidator(llm=llm)

    print("🔍 개별 청크 검증 테스트:")
    print("=" * 60)

    for chunk in sample_chunks:
        validation = validator.validate_chunk(chunk)
        print(f"\n청크 {validation['chunk_index']}: {validation['severity'].upper()}")
        print(f"텍스트: {validation['text_preview']}")
        
        if validation.get("typo_validation", {}).get("has_typos"):
            print("❌ 오타 발견:")
            print(validation["typo_validation"]["typo_findings"][:200])
        
        if validation.get("logic_validation", {}).get("has_logic_errors"):
            print("⚠️  논리적 오류 발견:")
            print(validation["logic_validation"]["logic_findings"][:200])

    # Full validation
    print("\n\n📋 전체 검증 결과:")
    print("=" * 60)
    result = validator.validate_all_chunks(sample_chunks, verbose=True)
    report = format_validation_report(result)
    print(report)


def test_validator_with_directory(pdf_dir: str):
    """Test validator with actual PDF directory"""
    print(f"📁 PDF 디렉토리 검증: {pdf_dir}")
    print("=" * 60)
    
    result = validate_pdfs_simple(
        pdf_dir, chunk_size=1000, overlap=300, verbose=True
    )
    report = format_validation_report(result)
    print(report)


if __name__ == "__main__":
    # Test 1: Sample Korean text
    test_validator_with_sample_text()
    
    # Test 2: Uncomment to test with actual PDFs
    # test_validator_with_directory("/path/to/pdf/directory")