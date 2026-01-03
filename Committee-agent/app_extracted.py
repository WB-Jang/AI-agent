import streamlit as st
import os
import tempfile
import docx
from read_docx_util import read_docx
from pdf_converter import batch_convert_to_pdf  # [추가] 방금 만든 변환 모듈 임포트
from PyPDF2 import PdfReader
from highlighting import highlight_errors

# --- LangChain 관련 임포트 (기존 유지) ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import re  # [필수] 이 줄이 없으면 에러가 납니다.

# [추가할 함수] 마크다운 문법 무시하고 글자 크기 유지하는 함수
def escape_markdown_special_chars(text):
    if not text: return text
    # 1. 색상 코드(#RRGGBB)가 아닌 '#'만 찾아서 변환 (제목으로 변하는 것 방지)
    text = re.sub(r'#(?![0-9a-fA-F]{3,6})', '&#35;', text)
    # 2. 볼드체/기울임꼴(*, _) 방지
    text = text.replace('*', '&#42;').replace('_', '&#95;')
    return text

# --- 기존 함수들 (read_raw_docx, read_pdf, get_proofreading_chain) ---
def read_raw_docx(file_path):
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"파일을 읽는 중 오류가 발생했습니다: {str(e)}"

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def get_proofreading_chain(api_key):
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0, openai_api_key=api_key)
    template = """
    당신은 한국어 교정 전문가입니다. 아래 텍스트에서 오타, 비문, 어색한 표현을 찾아주세요.

    [텍스트]:
    {text}

    [응답 형식]:
    반드시 아래와 같은 **JSON 포맷**으로만 응답하세요. 다른 말은 하지 마세요.
    오류가 없으면 빈 리스트 [] 를 반환하세요.

    [
      {{
        "error_sentence": "오류가 포함된 원본 문장 또는 단어 구절 (원본 텍스트와 정확히 일치해야 함)",
        "correction": "수정 제안 내용",
        "reason": "수정 이유"
      }},
      ...
    ]
    """
    prompt = PromptTemplate.from_template(template)
    return prompt | llm | StrOutputParser()

# --- 메인 함수 ---
def main():

    st.set_page_config(page_title="Word/PPT 통합 플랫폼", layout='wide')

    if "proofreading_results" not in st.session_state:
        st.session_state.proofreading_results = None

    # [추가] 왼쪽 미리보기 화면용 상태 변수
    if "highlighted_preview" not in st.session_state:
        st.session_state.highlighted_preview = None

    st.title("문서 작업 통합 도구 (Correction & Conversion)")

    # [UI 구조 변경] 탭을 사용하여 기능 분리
    tab1, tab2 = st.tabs(["📄 문서 오타 검수", "🔄 PDF 일괄 변환"])

    # =========================================================
    # TAB 1: 기존 오타 검수 기능
    # =========================================================
    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("1. 파일 업로드 및 확인")
            openai_api_key = st.text_input("OpenAI API Key", type="password", key="api_key_tab1")
            uploaded_file = st.file_uploader("검수할 파일 업로드 (Word/PDF)", type=["docx", "pdf"], key="uploader_tab1")

            if uploaded_file is not None:
                # 임시 파일 처리 (기존 코드 유지)
                suffix = '.docx' if uploaded_file.name.endswith('.docx') else '.pdf'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                # [수정] 미리보기 로직 변경
                # 원본 텍스트 읽기
                if suffix == '.docx':
                    raw_text = read_raw_docx(tmp_file_path)
                else:
                    raw_text = read_pdf(uploaded_file)

                # 검수 결과(하이라이팅)가 있으면 그것을 보여주고, 없으면 원본 텍스트를 보여줌
                if st.session_state.highlighted_preview:
                    st.markdown("⬇️ **오타가 감지된 문장이 빨갛게 표시됩니다.**")

                    preview_content = st.session_state.highlighted_preview

                    # CSS로 폰트 크기(14px)를 강제로 고정합니다.
                    st.markdown(
                        f"""
                        <div style="
                            height: 400px;
                            overflow-y: scroll;
                            border: 1px solid #dee2e6;
                            padding: 15px;
                            border-radius: 0.25rem;
                            background-color: #ffffff;
                            color: #31333F;
                            font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                            font-size: 14px;
                            line-height: 1.6;">
                            {preview_content}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.text_area("내용 미리보기", raw_text, height=400)

        with col2:
            st.subheader("2. AI 검수 결과")
            if uploaded_file and suffix == '.docx':
                if st.button("오타 검수 시작", type="primary"):
                    if not openai_api_key:
                        st.error("API Key를 입력해주세요.")
                    else:
                        # ... (기존 초기화 코드) ...
                        sections = read_docx(tmp_file_path)
                        chain = get_proofreading_chain(openai_api_key)

                        results = []
                        full_highlighted_content = []  # [추가] 전체 문서를 재조립할 리스트

                        progress_bar = st.progress(0)

                        for i, section in enumerate(sections):
                            title = section.get('title', '제목 없음')
                            content = section.get('content', '')

                            try:
                                response_json = chain.invoke({"text": content})
                                # 하이라이팅 함수 호출
                                highlighted_text, errors = highlight_errors(content, response_json)

                                # 1. 글자가 커지는 것을 막기 위해 특수문자 처리 함수 통과
                                safe_highlighted = escape_markdown_special_chars(highlighted_text)

                                # 2. <h4> 태그 대신, 폰트 크기를 16px로 고정한 div 사용
                                section_html = f"""
                                <div style="margin-bottom: 20px;">
                                    <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px; border-bottom: 2px solid #eee; padding-bottom: 3px;">
                                        {title}
                                    </div>
                                    <div style="font-size: 14px; line-height: 1.6; color: #444;">
                                        {safe_highlighted}
                                    </div>
                                </div>
                                """
                                full_highlighted_content.append(section_html)

                            except Exception as e:
                                results.append({"title": title, "correction": f"에러: {e}"})
                                full_highlighted_content.append(f"<h4>{title}</h4>{content}<br>") # 에러 시 원본 유지

                            progress_bar.progress((i + 1) / len(sections))

                        st.session_state.proofreading_results = results

                        # [핵심] 분석이 끝나면 누적된 HTML을 세션 상태에 저장 -> 왼쪽 화면 갱신됨
                        st.session_state.highlighted_preview = "\n".join(full_highlighted_content)

                        progress_bar.empty()

                        # Streamlit 특성상 상태값 변경 후 즉시 UI 반영을 위해 rerun이 필요할 수 있음
                        st.rerun()

            # 결과 출력 루프 (app.py 하단부)
            if st.session_state.proofreading_results:
                st.markdown("---")
                st.subheader("📋 AI 수정 제안 요약")

                for res in st.session_state.proofreading_results:
                    # 각 섹션(문단 제목)별로 접고 펼칠 수 있는 영역 생성
                    with st.expander(f"📌 {res['title']}", expanded=True):

                        errors = res.get('errors', [])

                        # 1. 수정 사항이 없는 경우 깔끔하게 표시
                        if not errors:
                            st.markdown(
                                """
                                <div style='padding: 10px; background-color: #f0fdf4; color: #15803d; border-radius: 5px; border: 1px solid #bbf7d0;'>
                                    ✅ 발견된 오타나 수정 사항이 없습니다. 완벽합니다!
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # 2. 수정 사항이 있는 경우 (카드 형태로 나열)
                        else:
                            for idx, error in enumerate(errors):
                                # 데이터 가져오기 (없을 경우 빈칸 처리)
                                original_txt = error.get('error_sentence', '')
                                correction_txt = error.get('correction', '')
                                reason_txt = error.get('reason', '')

                                # 마크다운(#, *) 오작동 방지용 이스케이프 (이전 단계에서 만든 함수 활용 권장)
                                # 만약 함수가 없다면 이 부분은 생략 가능하지만, 안전을 위해 추천합니다.
                                # original_txt = escape_markdown_special_chars(original_txt)
                                # correction_txt = escape_markdown_special_chars(correction_txt)

                                # 스타일링된 HTML 카드 출력
                                st.markdown(f"""
                                <div style="
                                    background-color: white;
                                    border: 1px solid #e5e7eb;
                                    border-radius: 8px;
                                    padding: 15px;
                                    margin-bottom: 12px;
                                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                                ">
                                    <div style="margin-bottom: 8px; font-size: 1.05em; line-height: 1.5;">
                                        <span style="background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-decoration: line-through;">
                                            {original_txt}
                                        </span>
                                        <span style="margin: 0 8px; color: #6b7280;">➡️</span>
                                        <span style="background-color: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                                            {correction_txt}
                                        </span>
                                    </div>

                                    <div style="
                                        background-color: #f9fafb;
                                        padding: 10px;
                                        border-radius: 6px;
                                        font-size: 0.9em;
                                        color: #4b5563;
                                        border-left: 3px solid #6366f1;
                                    ">
                                        <strong>💡 수정 이유:</strong> {reason_txt}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
    # =========================================================
    # TAB 2: [신규] PDF 일괄 변환 기능
    # =========================================================
    with tab2:
        st.header("📂 Word/PPT -> PDF 일괄 변환")
        st.markdown("""
        - 지정한 폴더에 있는 **모든 .docx, .pptx 파일**을 PDF로 변환합니다.
        - **주의:** 서버(Linux)에 LibreOffice와 한글 폰트가 설치되어 있어야 정상 동작합니다.
        """)

        # 기본값을 현재 작업 경로로 설정
        default_path = os.getcwd()
        target_folder = st.text_input("변환할 파일이 있는 폴더 경로를 입력하세요:", value=default_path)

        if st.button("일괄 변환 시작", type="primary"):
            st.write("---")
            log_area = st.empty()

            # 제너레이터(yield)로부터 메시지를 받아 실시간 출력
            for msg_type, msg in batch_convert_to_pdf(target_folder):
                if msg_type == "Error":
                    st.error(msg)
                elif msg_type == "Success":
                    st.success(msg)
                elif msg_type == "Info":
                    st.info(msg)
                elif msg_type == "Progress":
                    with log_area:
                        st.write(f"⏳ {msg}")

            st.success("모든 작업이 종료되었습니다.")
            log_area.empty()

if __name__ == "__main__":
    main()