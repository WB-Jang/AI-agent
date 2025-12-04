# word_parsing_new.py - 통합 문서 처리 시스템

## 개요
`word_parsing_new.py`는 `_faiss.py`와 `word2pdf.py`의 기능을 통합하여 Word 문서를 처리하고 FAISS 벡터 데이터베이스를 구축하는 통합 솔루션입니다.

## 주요 기능

### 1. 통합된 기능
- **word_parsing_new.py (메인)**: LangChain 기반 문서 파싱 및 멀티-벡터 검색
- **_faiss.py**: 로컬 임베딩 서버 지원 추가
- **word2pdf.py**: 폴더 내 파일 탐색 로직 통합

### 2. 주요 특징

#### 임베딩 모델 선택
- **OpenAI 임베딩**: `USE_LOCAL_EMBEDDING = False`
- **로컬 임베딩 서버**: `USE_LOCAL_EMBEDDING = True` (llama-server 사용)

#### 처리 모드
- **단일 파일 모드**: 특정 문서 하나를 처리
- **배치 모드**: 폴더 내 모든 .docx/.doc 파일을 자동으로 처리

#### 문서 구조 파싱
- 제목(Title), 표(Table), 일반 텍스트 자동 분류
- 표 내용 요약 (LLM 기반)
- 청킹 및 벡터화
- Multi-Vector Retriever 구축

## 사용 방법

### 1. 단일 파일 처리 (OpenAI 임베딩)
```python
retriever = main(
    doc_path="./sample_document.docx",
    folder_path=None,
    force_rebuild=False,
    use_local=False
)
```

### 2. 폴더 내 모든 파일 처리
```python
retrievers = main(
    folder_path="./documents",
    force_rebuild=False,
    use_local=False
)
```

### 3. 로컬 임베딩 서버 사용
```python
# 먼저 로컬 서버를 실행해야 합니다:
# llama-server.exe -m "path/to/bge-m3-FP16.gguf" --embedding -t 8 -c 4092 -b 2048 -ub 2048 -np 1 -v --host 0.0.0.0 --port 8081

retriever = main(
    doc_path="./sample_document.docx",
    folder_path=None,
    force_rebuild=False,
    use_local=True
)
```

## 설정값

```python
DEFAULT_DOC_PATH = "./sample_document.docx"
DEFAULT_FOLDER_PATH = None  # 폴더 경로 (None이면 단일 파일 모드)
DB_PATH = "faiss_db_hybrid"
DOCSTORE_PATH = "docstore.pkl"
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
LLM_MODEL_NAME = "gpt-3.5-turbo"
USE_LOCAL_EMBEDDING = False  # True로 설정 시 로컬 서버 사용
LOCAL_EMBEDDING_SERVER = "http://127.0.0.1:8081"
```

## 통합된 클래스 및 함수

### LocalEmbeddings 클래스 (from _faiss.py)
- 로컬 llama-server를 사용한 임베딩 생성
- LangChain Embeddings 인터페이스 구현

### get_word_files() 함수 (from word2pdf.py)
- 폴더 내 .docx/.doc 파일 자동 탐색
- 임시 파일(~$로 시작) 자동 제외

### process_folder() 함수 (신규)
- 폴더 내 모든 문서 배치 처리
- 각 문서별 독립적인 FAISS DB 생성
- 진행 상황 출력 및 에러 핸들링

## 파일 구조

```
Committee-agent/file-preprocessing/
├── word_parsing_new.py  # 통합 메인 파일
├── _faiss.py           # (참조용) 로컬 임베딩 로직
├── word2pdf.py         # (참조용) 파일 탐색 로직
└── README_word_parsing_new.md
```

## 의존성

```python
# 핵심 라이브러리
- langchain-community
- langchain-openai
- langchain-core
- langchain-text-splitters
- faiss-cpu (또는 faiss-gpu)
- unstructured[docx]
- numpy
- requests (로컬 임베딩 서버 사용 시)
```

## 변경 사항

### 기존 word_parsing_new.py에서 추가된 기능:
1. ✅ 로컬 임베딩 서버 지원 (LocalEmbeddings 클래스)
2. ✅ 폴더 내 파일 자동 탐색 (get_word_files 함수)
3. ✅ 배치 처리 기능 (process_folder 함수)
4. ✅ 유연한 설정 옵션 (use_local, folder_path 파라미터)
5. ✅ 개선된 에러 핸들링

### 버그 수정:
- `docstore. pkl` → `docstore.pkl`
- `doc. metadata` → `doc.metadata`
- `table_content. strip()` → `table_content.strip()`
- `uuid. uuid4()` → `uuid.uuid4()`

## 테스트

파일 처리 후 자동으로 검색 테스트 실행:
- "표에 대한 정보를 알려줘"
- "문서의 주요 섹션은 무엇인가요?"

## 주의사항

1. **로컬 임베딩 서버 사용 시**: 먼저 llama-server를 포트 8081에서 실행해야 합니다
2. **OpenAI API 사용 시**: OPENAI_API_KEY 환경 변수 설정 필요
3. **배치 모드**: 각 파일마다 별도의 FAISS DB가 생성됩니다 (메모리 사용량 고려)
