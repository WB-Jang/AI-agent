```markdown
# Text Validator — 오타 및 논리적 오류 검증 모듈

PDF 청크 텍스트에서 오타, 문법 오류, 논리적 불일치를 감지하는 LLM 기반 검증 시스템입니다.

## 파일 구성

- **text_validator.py**: 핵심 검증 로직 (LangChain 기반)
  - `TextValidator` 클래스: 오타/논리 오류 감지
  - `validate_chunk()`: 개별 청크 검증
  - `validate_all_chunks()`: 전체 청크 검증 및 집계

- **langgraph_validator.py**: LangGraph 워크플로우 오케스트레이션
  - `create_validation_graph()`: LangGraph 생성
  - `run_validation_workflow()`: 워크플로우 실행
  - 조건부 라우팅 및 에러 처리

- **validation_pipeline.py**: 전체 파이프라인 통합
  - `validate_pdfs_simple()`: LangChain 기반 간단한 검증
  - `validate_pdfs_with_graph()`: LangGraph 기반 고급 검증
  - CLI 인터페이스

- **test_validator.py**: 테스트 및 예제

## 사용 방법

### 1. 간단한 검증 (LangChain)

```python
from validation_pipeline import validate_pdfs_simple
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(temperature=0, model="gpt-4")
result = validate_pdfs_simple(
    "/path/to/pdfs",
    chunk_size=1000,
    overlap=300,
    llm=llm,
    verbose=True
)
```

### 2. 고급 검증 (LangGraph)

```python
from validation_pipeline import validate_pdfs_with_graph

result = validate_pdfs_with_graph(
    "/path/to/pdfs",
    chunk_size=1000,
    overlap=300,
    verbose=True
)
```

### 3. CLI 사용

```bash
# 간단한 모드
python Committee-agent/validation_pipeline.py /path/to/pdfs --mode simple --verbose

# LangGraph 모드 (고급)
python Committee-agent/validation_pipeline.py /path/to/pdfs --mode graph --verbose

# 결과를 파일로 저장
python Committee-agent/validation_pipeline.py /path/to/pdfs \
  --mode simple \
  --output validation_report.json \
  --chunk-size 1000 \
  --overlap 300
```

## 반환 형식

```json
{
  "chunk_validations": [
    {
      "chunk_index": 0,
      "source": "document.pdf",
      "text_preview": "...",
      "typo_validation": {
        "has_typos": false,
        "typo_findings": "오류 없음",
        "error_count": 0
      },
      "logic_validation": {
        "has_logic_errors": true,
        "logic_findings": "...",
        "error_count": 2
      },
      "is_valid": false,
      "severity": "warning",
      "metadata": {...}
    }
  ],
  "summary": {
    "total_chunks": 10,
    "clean_chunks": 7,
    "warning_chunks": 2,
    "critical_chunks": 1,
    "overall_quality_score": 0.7
  },
  "aggregate_findings": "..."
}
```

## 심각도 레벨

- **clean**: 오류 없음
- **warning**: 약간의 오류 발견 (1~5개)
- **critical**: 심각한 오류 (5개 이상 또는 논리 오류 3개 이상)

## 커스터마이징

### 프롬프트 템플릿 변경

```python
from text_validator import TextValidator

custom_typo_prompt = """당신의 커스텀 프롬프트..."""
validator = TextValidator(
    typo_prompt_template=custom_typo_prompt
)
```

### LLM 모델 변경

```python
from langchain.chat_models import ChatAnthropic

llm = ChatAnthropic(model="claude-2")
result = validate_pdfs_simple("/path/to/pdfs", llm=llm)
```

## 완전한 파이프라인 통합

```python
from pdf_loader import load_and_chunk_pdfs
from text_validator import TextValidator
from llm_summarizer import summarize_chunks
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(temperature=0)

# 1단계: PDF 로드 및 청크 분할
chunks = load_and_chunk_pdfs("/path/to/pdfs", chunk_size=1000, overlap=300)

# 2단계: 검증 (오타/논리 오류)
validator = TextValidator(llm=llm)
validation_result = validator.validate_all_chunks(chunks)

# 3단계: 요약 (유효한 청크만)
valid_chunks = [c for c in chunks if validation_result['summary']['clean_chunks'] > 0]
summary_result = summarize_chunks(valid_chunks, llm=llm)

print(f"Quality: {validation_result['summary']['overall_quality_score']}")
print(f"Summary: {summary_result['final_summary']}")
```

## 환경 설정

```bash
export OPENAI_API_KEY="your-api-key"
```

## 주의사항

- 첫 API 호출이 느릴 수 있습니다 (LLM 초기화).
- 많은 청크의 경우 비용이 높아질 수 있습니다.
- 검증 정확도는 LLM 성능에 의존합니다.

## 개선 사항

- 다양한 언어 지원 (현재 한국어 중심)
- 캐싱을 통한 성능 개선
- 병렬 처리 지원
- 커스텀 규칙 엔진 추가
```