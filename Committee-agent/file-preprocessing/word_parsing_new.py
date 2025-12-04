import uuid
import os

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

# ==========================================
# 1. 설정 및 모델 준비
# ==========================================
# OpenAI API 키 설정 (환경변수에 있다면 생략 가능)
# os.environ["OPENAI_API_KEY"] = "sk-..."

# 임베딩 모델: 한국어 성능을 위해 ko-sroberta 등을 써도 되지만,
# 편의상 OpenAIEmbeddings로 통일했습니다. (필요시 HuggingFaceEmbeddings로 교체 가능)
embedding_model = OpenAIEmbeddings()

# 표 요약용 LLM (빠르고 저렴한 모델 권장)
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

# ==========================================
# 2. 문서 로드 (구조 인식 모드)
# ==========================================
print("문서 로딩 중...")
loader = UnstructuredWordDocumentLoader(
"./sample_document.docx",
mode="elements", # 요소 단위 분할
strategy="hi_res" # 표 구조 인식 활성화
)
raw_docs = loader.load()

# ==========================================
# 3. 구조적 파싱 및 문맥 주입 (Code 1의 논리)
# ==========================================
print("구조 파싱 및 분류 중...")

processed_texts = [] # 일반 텍스트 보관용
raw_tables = [] # 표 원본(HTML) 보관용
current_section = "Introduction" # 초기 섹션값

for doc in raw_docs:
category = doc.metadata.get("category")

# 3-1. 제목(Title) 처리: 섹션 추적
if category == "Title":
current_section = doc.page_content
# 제목도 검색 대상에 포함 (문맥 추가)
new_content = f"[Header] {doc.page_content}"
doc.page_content = new_content
processed_texts.append(doc)

# 3-2. 표(Table) 처리: 별도 리스트로 분리
elif category == "Table":
# 표는 문맥 주입 대신, 메타데이터에 섹션 정보만 남기고 별도 처리
doc.metadata["related_section"] = current_section
# text_as_html이 있으면 우선 사용, 없으면 텍스트 사용
doc.page_content = doc.metadata.get("text_as_html", doc.page_content)
raw_tables.append(doc)

# 3-3. 일반 텍스트 처리: 문맥(Section) 주입
else:
# 1.1. 등의 번호 매기기 구조 아래에 있는 텍스트에 상위 제목을 붙임
new_content = f"[Section: {current_section}] {doc.page_content}"
doc.page_content = new_content
processed_texts.append(doc)

# ==========================================
# 4. 표 요약 (Code 2의 논리)
# ==========================================
print(f"{len(raw_tables)}개의 표를 요약 중입니다...")

summarize_prompt = ChatPromptTemplate.from_template(
"""
다음은 문서의 '{section}' 섹션에 포함된 표입니다.
이 표가 검색될 수 있도록 자연어로 상세히 요약해주세요.

[표 내용]:
{element}
"""
)
summarize_chain = summarize_prompt | llm | StrOutputParser()

# 표 요약 실행 (Batch)
# 입력 데이터 준비: 섹션 정보와 표 내용을 함께 전달
table_inputs = [{"element": t.page_content, "section": t.metadata.get("related_section")} for t in raw_tables]
table_summaries = summarize_chain.batch(table_inputs, {"max_concurrency": 5})

# ==========================================
# 5. Multi-Vector Retriever 저장소 구축
# ==========================================
# 5-1. 저장소 초기화
vectorstore = FAISS.from_documents(
[Document(page_content="init", metadata={})],
embedding_model
)
# 실제 서비스에서는 RedisStore 등 영구 저장소 권장 (여기선 메모리 사용)
docstore = InMemoryStore()
id_key = "doc_id"

retriever = MultiVectorRetriever(
vectorstore=vectorstore,
docstore=docstore,
id_key=id_key,
)

# 5-2. 데이터 저장 로직

# (A) 표 데이터 저장
# - VectorStore: "요약본" 저장
# - DocStore: "원본(HTML)" 저장
table_ids = [str(uuid.uuid4()) for _ in raw_tables]

summary_docs = [
Document(page_content=s, metadata={id_key: table_ids[i], "type": "table_summary"})
for i, s in enumerate(table_summaries)
]

# 원본 표 저장 시 메타데이터 유지
retriever.vectorstore.add_documents(summary_docs)
retriever.docstore.mset(list(zip(table_ids, raw_tables)))

# (B) 텍스트 데이터 저장
# - VectorStore: "문맥 주입된 텍스트" 저장
# - DocStore: "문맥 주입된 텍스트" 저장 (텍스트는 원본과 검색본이 동일)
text_ids = [str(uuid.uuid4()) for _ in processed_texts]

# 텍스트도 너무 길면 잘라야 하므로 Splitter 적용
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
# (이미 split되어 있을 수 있지만, 안전장치로 한 번 더 체크하거나 그대로 사용)
# 여기서는 processed_texts가 이미 요소 단위이므로 그대로 ID 매핑만 진행
text_docs_with_ids = []
for i, doc in enumerate(processed_texts):
doc.metadata[id_key] = text_ids[i]
text_docs_with_ids.append(doc)

retriever.vectorstore.add_documents(text_docs_with_ids)
retriever.docstore.mset(list(zip(text_ids, processed_texts)))

print("모든 데이터 저장 및 인덱싱 완료!")

# ==========================================
# 6. 로컬 저장 및 테스트
# ==========================================

# FAISS 인덱스 로컬 저장
vectorstore.save_local("faiss_db_hybrid")
print("Faiss DB 저장 완료 (faiss_db_hybrid 폴더)")

# 검색 테스트
query = "특정 표에 대한 내용을 물어보세요"
print(f"\nQuery: {query}")
results = retriever.invoke(query)

if results:
print("\n--- 검색 결과 (Top 1) ---")
top_doc = results[0]
print(f"Type: {top_doc.metadata.get('category', 'Text')}")
print(f"Section Info: {top_doc.metadata.get('related_section', 'N/A')}")
print(f"Content (Preview): {top_doc.page_content[:300]}") # 표라면 HTML이 출력됨
else:
print("검색 결과가 없습니다.")
