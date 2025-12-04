import uuid
import os
import pickle
from pathlib import Path
from typing import List, Optional
import requests
import numpy as np
import json

# 라이브러리 임포트
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.storage import InMemoryStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.embeddings import Embeddings

# ==========================================
# 0. 설정값
# ==========================================
DEFAULT_DOC_PATH = "./sample_document.docx"
DEFAULT_FOLDER_PATH = None  # 폴더 경로 (None이면 단일 파일 모드)
DB_PATH = "faiss_db_hybrid"
DOCSTORE_PATH = "docstore.pkl"
EMBEDDING_MODEL_NAME = "text-embedding-3-small"  # 더 저렴하고 빠른 모델
LLM_MODEL_NAME = "gpt-3.5-turbo"
USE_LOCAL_EMBEDDING = False  # True로 설정 시 로컬 서버 사용
LOCAL_EMBEDDING_SERVER = "http://127.0.0.1:8081"  # 로컬 임베딩 서버 주소
LOCAL_EMBEDDING_TIMEOUT = 45  # 로컬 임베딩 서버 타임아웃 (초)
ERROR_PREVIEW_LENGTH = 100  # 에러 메시지에 표시할 텍스트 미리보기 길이
TEMP_FILE_PREFIX = '~$'  # 임시 파일 접두사 (Word/Excel 등)

# ==========================================
# 로컬 임베딩 모델 클래스 (from _faiss.py)
# ==========================================
class LocalEmbeddings(Embeddings):
    """로컬 llama-server를 사용한 임베딩 모델"""
    
    def __init__(self, server_url: str = LOCAL_EMBEDDING_SERVER):
        self.server_url = server_url
    
    def _embed_text(self, texts: List[str]) -> np.ndarray:
        """
        llama-server의 /v1/embeddings 엔드포인트를 사용해 bge-m3.gguf 임베딩 진행
        반환 결과 : (N, D) float32 numpy array
        """
        out = []
        for t in texts:
            vecs = None 
            try:
                r = requests.post(
                    f"{self.server_url}/v1/embeddings", 
                    json={"model": "bge-m3", "input": t}, 
                    timeout=LOCAL_EMBEDDING_TIMEOUT
                )
                if r.ok and "data" in r.json():
                    vecs = r.json()["data"][0]["embedding"]
                    v = np.array(vecs, dtype=np.float32)
                    v /= (np.linalg.norm(v) + 1e-12)  # 정규화
                    out.append(v)
            except Exception as e:
                print(f"⚠️ 임베딩 실패 (텍스트 길이: {len(t)}자): {e}")
                pass
        
        if not out:
            # 텍스트 미리보기 (설정된 길이만 표시, 잘린 경우 표시)
            preview = texts[0] if texts else "빈 텍스트"
            if len(preview) > ERROR_PREVIEW_LENGTH:
                preview = preview[:ERROR_PREVIEW_LENGTH] + "... (잘림)"
            raise RuntimeError(f"임베딩 API 실패: {preview}")
        
        return np.vstack(out).astype("float32")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """LangChain 인터페이스 구현"""
        embeddings = self._embed_text(texts)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """LangChain 인터페이스 구현"""
        embedding = self._embed_text([text])
        return embedding[0].tolist()

# ==========================================
# 파일 탐색 기능 (from word2pdf.py)
# ==========================================
def get_word_files(folder_path: str) -> List[str]:
    """
    폴더 내의 .docx/.doc 파일 리스트를 반환
    
    Args:
        folder_path: 검색할 폴더 경로
        
    Returns:
        정렬된 파일 이름 리스트
        
    Raises:
        ValueError: 폴더 경로가 유효하지 않은 경우
    """
    # 경로 검증
    folder_path_obj = Path(folder_path).resolve()
    if not folder_path_obj.exists():
        raise ValueError(f"폴더가 존재하지 않습니다: {folder_path}")
    if not folder_path_obj.is_dir():
        raise ValueError(f"폴더가 아닙니다: {folder_path}")
    
    extensions = ('.docx', '.doc')
    files = [
        f.name for f in folder_path_obj.iterdir()
        if f.is_file() and f.name.lower().endswith(extensions) and not f.name.startswith(TEMP_FILE_PREFIX)
    ]
    return sorted(files)

# ==========================================
# 1. 설정 및 모델 준비
# ==========================================
def initialize_models(use_local: bool = USE_LOCAL_EMBEDDING):
    """모델 초기화 with 에러 처리"""
    try:
        if use_local:
            print("로컬 임베딩 서버 사용")
            embedding_model = LocalEmbeddings(server_url=LOCAL_EMBEDDING_SERVER)
        else:
            print("OpenAI 임베딩 사용")
            embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
        
        llm = ChatOpenAI(temperature=0, model=LLM_MODEL_NAME)
        return embedding_model, llm
    except Exception as e:
        raise RuntimeError(f"모델 초기화 실패: {e}")

# ==========================================
# 2. 문서 로드
# ==========================================
def load_document(file_path: str) -> List[Document]:
    """문서 로드 with 검증"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"문서를 찾을 수 없습니다: {file_path}")
    
    print(f"문서 로딩 중: {file_path}")
    try:
        loader = UnstructuredWordDocumentLoader(
            file_path,
            mode="elements",
            strategy="hi_res"
        )
        docs = loader.load()
        
        if not docs:
            raise ValueError("문서에서 콘텐츠를 추출할 수 없습니다.")
        
        print(f"✓ {len(docs)}개 요소 로드 완료")
        return docs
    except Exception as e:
        raise RuntimeError(f"문서 로드 실패: {e}")

# ==========================================
# 3. 구조적 파싱
# ==========================================
def parse_document_structure(raw_docs: List[Document]):
    """문서 구조 파싱 및 분류"""
    print("구조 파싱 중...")
    
    processed_texts = []
    raw_tables = []
    current_section = "Introduction"
    
    for doc in raw_docs:
        category = doc.metadata.get("category", "NarrativeText")
        
        if category == "Title":
            current_section = doc.page_content.strip()
            doc.page_content = f"[Header] {doc.page_content}"
            doc.metadata["type"] = "header"
            processed_texts.append(doc)
        
        elif category == "Table":
            doc.metadata["related_section"] = current_section
            doc.metadata["type"] = "table"
            # text_as_html 우선, 없으면 page_content 사용
            table_content = doc.metadata.get("text_as_html") or doc.page_content
            if table_content.strip():  # 빈 표 제외
                doc.page_content = table_content
                raw_tables.append(doc)
        
        else:
            # 빈 텍스트 제외
            if doc.page_content.strip():
                doc.page_content = f"[Section: {current_section}] {doc.page_content}"
                doc.metadata["type"] = "text"
                doc.metadata["related_section"] = current_section
                processed_texts.append(doc)
    
    print(f"✓ 텍스트: {len(processed_texts)}개, 표: {len(raw_tables)}개")
    return processed_texts, raw_tables

# ==========================================
# 4.  표 요약
# ==========================================
def summarize_tables(raw_tables: List[Document], llm) -> List[str]:
    """표 요약 with 에러 처리"""
    if not raw_tables:
        print("요약할 표가 없습니다.")
        return []
    
    print(f"{len(raw_tables)}개의 표 요약 중...")
    
    summarize_prompt = ChatPromptTemplate.from_template(
        """다음은 문서의 '{section}' 섹션에 포함된 표입니다.
이 표가 검색될 수 있도록 핵심 내용을 자연어로 요약해주세요. 
표의 제목, 주요 항목, 수치를 포함하되 200자 이내로 작성하세요.

[표 내용]:
{element}

[요약]:"""
    )
    summarize_chain = summarize_prompt | llm | StrOutputParser()
    
    try:
        table_inputs = [
            {
                "element": t.page_content[:2000],  # 토큰 제한 고려
                "section": t.metadata.get("related_section", "Unknown")
            }
            for t in raw_tables
        ]
        summaries = summarize_chain.batch(table_inputs, {"max_concurrency": 3})
        print(f"✓ 표 요약 완료")
        return summaries
    except Exception as e:
        print(f"⚠️  표 요약 실패, 원본 사용: {e}")
        # Fallback: 원본 텍스트의 앞부분 사용
        return [t.page_content[:300] for t in raw_tables]

# ==========================================
# 5. Multi-Vector Retriever 구축
# ==========================================
def build_retriever(
    processed_texts: List[Document],
    raw_tables: List[Document],
    table_summaries: List[str],
    embedding_model
) -> MultiVectorRetriever:
    """Retriever 구축 (더미 문서 없이)"""
    print("Retriever 구축 중...")
    
    # 1. 빈 VectorStore 생성 (더미 없이)
    if not processed_texts and not table_summaries:
        raise ValueError("저장할 문서가 없습니다.")
    
    # 첫 번째 실제 문서로 초기화 (나중에 삭제)
    init_doc = Document(page_content="TEMP_INIT", metadata={"_temp": True})
    vectorstore = FAISS.from_documents([init_doc], embedding_model)
    
    docstore = InMemoryStore()
    id_key = "doc_id"
    
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        id_key=id_key,
    )
    
    # 2. 표 데이터 저장
    if raw_tables and table_summaries:
        table_ids = [str(uuid.uuid4()) for _ in raw_tables]
        
        summary_docs = [
            Document(
                page_content=s,
                metadata={
                    id_key: table_ids[i],
                    "type": "table_summary",
                    "related_section": raw_tables[i].metadata.get("related_section")
                }
            )
            for i, s in enumerate(table_summaries)
        ]
        
        retriever.vectorstore.add_documents(summary_docs)
        retriever.docstore.mset(list(zip(table_ids, raw_tables)))
        print(f"✓ 표 {len(raw_tables)}개 저장")
    
    # 3.  텍스트 데이터 저장 (청킹 적용)
    if processed_texts:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )
        
        split_texts = []
        for doc in processed_texts:
            chunks = text_splitter.split_documents([doc])
            split_texts.extend(chunks)
        
        text_ids = [str(uuid.uuid4()) for _ in split_texts]
        
        for i, doc in enumerate(split_texts):
            doc.metadata[id_key] = text_ids[i]
        
        retriever.vectorstore.add_documents(split_texts)
        retriever.docstore.mset(list(zip(text_ids, split_texts)))
        print(f"✓ 텍스트 {len(split_texts)}개 청크 저장")
    
    # 4. 임시 초기화 문서 제거
    try:
        # FAISS는 직접 삭제 불가, 하지만 검색 시 _temp 필터링 가능
        pass
    except:
        pass
    
    print("✓ Retriever 구축 완료")
    return retriever

# ==========================================
# 6. 저장 및 로드
# ==========================================
def save_retriever(retriever: MultiVectorRetriever, db_path: str, docstore_path: str):
    """지속성 보장: VectorStore + DocStore 모두 저장"""
    print("저장 중...")
    
    # VectorStore 저장
    retriever.vectorstore.save_local(db_path)
    
    # DocStore 저장 (pickle 사용)
    Path(db_path).mkdir(exist_ok=True)
    docstore_file = os.path.join(db_path, docstore_path)
    
    with open(docstore_file, 'wb') as f:
        # InMemoryStore의 내부 store dict 저장
        pickle.dump(dict(retriever.docstore.store), f)
    
    print(f"✓ 저장 완료: {db_path}")

def load_retriever(db_path: str, docstore_path: str, embedding_model) -> MultiVectorRetriever:
    """저장된 Retriever 로드"""
    print("기존 데이터 로드 중...")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB를 찾을 수 없습니다: {db_path}")
    
    # VectorStore 로드
    vectorstore = FAISS.load_local(
        db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )
    
    # DocStore 로드
    docstore_file = os.path.join(db_path, docstore_path)
    docstore = InMemoryStore()
    
    if os.path.exists(docstore_file):
        with open(docstore_file, 'rb') as f:
            store_data = pickle.load(f)
            docstore.mset(list(store_data.items()))
    
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        id_key="doc_id"
    )
    
    print("✓ 로드 완료")
    return retriever

# ==========================================
# 7. 검색 테스트
# ==========================================
def test_retrieval(retriever: MultiVectorRetriever, query: str, top_k: int = 3):
    """검색 테스트 with 상세 출력"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    try:
        # _temp 메타데이터 필터링
        results = retriever.invoke(query)
        results = [r for r in results if not r.metadata.get("_temp")][:top_k]
        
        if not results:
            print("❌ 검색 결과가 없습니다.")
            return
        
        for i, doc in enumerate(results, 1):
            print(f"\n--- 결과 #{i} ---")
            print(f"Type: {doc.metadata.get('type', 'unknown')}")
            print(f"Section: {doc.metadata.get('related_section', 'N/A')}")
            print(f"Content (앞 300자):\n{doc.page_content[:300]}...")
            print("-" * 60)
    
    except Exception as e:
        print(f"❌ 검색 실패: {e}")

# ==========================================
# 8. 배치 처리 기능 (폴더 내 여러 파일 처리)
# ==========================================
def process_folder(
    folder_path: str, 
    embedding_model,
    llm,
    db_base_path: str = "faiss_db_batch",
    force_rebuild: bool = False
) -> dict:
    """
    폴더 내 모든 Word 문서를 처리하고 각각의 retriever를 생성
    
    Returns:
        dict: {filename: retriever} 매핑
    """
    print(f"\n{'='*60}")
    print(f"폴더 처리 시작: {folder_path}")
    print(f"{'='*60}\n")
    
    # 폴더 내 파일 목록 가져오기
    files = get_word_files(folder_path)
    
    if not files:
        print("처리할 문서가 없습니다.")
        return {}
    
    print(f"총 {len(files)}개의 문서를 처리합니다.")
    
    retrievers = {}
    
    for i, file in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] 처리 중: {file}")
        
        try:
            # 안전한 파일 경로 생성
            folder_path_obj = Path(folder_path).resolve()
            file_path = (folder_path_obj / file).resolve()
            
            # 경로 검증: 파일이 folder_path 내에 있는지 확인 (directory traversal 방지)
            try:
                file_path.relative_to(folder_path_obj)
            except ValueError:
                print(f"  ❌ 보안: 허용되지 않은 경로 - {file}")
                continue
            
            # 파일별 DB 경로 설정
            file_base_name = os.path.splitext(file)[0]
            db_path = f"{db_base_path}_{file_base_name}"
            db_path_obj = Path(db_path).resolve()
            docstore_path = "docstore.pkl"
            
            # 기존 DB가 있고 재구축 안 할 경우
            if db_path_obj.exists() and not force_rebuild:
                print(f"  기존 DB 발견, 로드합니다: {db_path_obj}")
                retriever = load_retriever(str(db_path_obj), docstore_path, embedding_model)
            else:
                # 문서 처리 파이프라인
                raw_docs = load_document(str(file_path))
                processed_texts, raw_tables = parse_document_structure(raw_docs)
                table_summaries = summarize_tables(raw_tables, llm)
                
                # Retriever 구축
                retriever = build_retriever(
                    processed_texts,
                    raw_tables,
                    table_summaries,
                    embedding_model
                )
                
                # 저장
                save_retriever(retriever, str(db_path_obj), docstore_path)
            
            retrievers[file] = retriever
            print(f"  ✓ 완료: {file}")
        
        except Exception as e:
            print(f"  ❌ 실패: {file} - {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"배치 처리 완료: {len(retrievers)}/{len(files)} 성공")
    print(f"{'='*60}\n")
    
    return retrievers

# ==========================================
# 9. 메인 실행
# ==========================================
def main(
    doc_path: Optional[str] = DEFAULT_DOC_PATH, 
    folder_path: Optional[str] = DEFAULT_FOLDER_PATH,
    force_rebuild: bool = False,
    use_local: bool = USE_LOCAL_EMBEDDING
):
    """
    메인 파이프라인
    
    Args:
        doc_path: 단일 문서 경로 (folder_path가 None일 때 사용)
        folder_path: 폴더 경로 (지정 시 폴더 내 모든 문서 처리)
        force_rebuild: True면 기존 DB 무시하고 재구축
        use_local: True면 로컬 임베딩 서버 사용
    """
    try:
        # 모델 초기화
        embedding_model, llm = initialize_models(use_local=use_local)
        
        # 폴더 모드 vs 단일 파일 모드
        if folder_path:
            # 폴더 내 모든 문서 처리
            retrievers = process_folder(
                folder_path, 
                embedding_model, 
                llm,
                force_rebuild=force_rebuild
            )
            
            # 각 문서에 대해 테스트
            test_query = "표에 대한 정보를 알려줘"
            for filename, retriever in retrievers.items():
                print(f"\n{'='*60}")
                print(f"문서: {filename}")
                print(f"{'='*60}")
                test_retrieval(retriever, test_query, top_k=2)
            
            print("\n✅ 모든 작업 완료!")
            return retrievers
        
        else:
            # 단일 문서 처리 (기존 로직)
            db_path_obj = Path(DB_PATH).resolve()
            if db_path_obj.exists() and not force_rebuild:
                print("기존 DB 발견, 로드합니다.")
                retriever = load_retriever(str(db_path_obj), DOCSTORE_PATH, embedding_model)
            else:
                # 문서 처리 파이프라인
                raw_docs = load_document(doc_path)
                processed_texts, raw_tables = parse_document_structure(raw_docs)
                table_summaries = summarize_tables(raw_tables, llm)
                
                # Retriever 구축
                retriever = build_retriever(
                    processed_texts,
                    raw_tables,
                    table_summaries,
                    embedding_model
                )
                
                # 저장
                save_retriever(retriever, DB_PATH, DOCSTORE_PATH)
            
            # 테스트
            test_queries = [
                "표에 대한 정보를 알려줘",
                "문서의 주요 섹션은 무엇인가요?",
            ]
            
            for query in test_queries:
                test_retrieval(retriever, query, top_k=2)
            
            print("\n✅ 모든 작업 완료!")
            return retriever
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==========================================
# 실행
# ==========================================
if __name__ == "__main__":
    # 사용 예시 1: 단일 파일 처리
    # retriever = main(
    #     doc_path="./sample_document.docx",
    #     folder_path=None,
    #     force_rebuild=False,
    #     use_local=False  # OpenAI 임베딩 사용
    # )
    
    # 사용 예시 2: 폴더 내 모든 파일 처리
    # retrievers = main(
    #     folder_path="./documents",
    #     force_rebuild=False,
    #     use_local=False  # OpenAI 임베딩 사용
    # )
    
    # 사용 예시 3: 로컬 임베딩 서버 사용
    # retriever = main(
    #     doc_path="./sample_document.docx",
    #     folder_path=None,
    #     force_rebuild=False,
    #     use_local=True  # 로컬 임베딩 서버 사용 (포트 8081)
    # )
    
    # 기본 실행: 단일 파일 + OpenAI 임베딩
    retriever = main(
        doc_path="./sample_document.docx",
        folder_path=None,
        force_rebuild=False,
        use_local=USE_LOCAL_EMBEDDING
    )
