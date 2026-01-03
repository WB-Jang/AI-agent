# 문서 작업 통합 도구 (Document Correction & Conversion Platform)

## 📖 개요

이 프로젝트는 Word 문서의 오타 검수와 Office 문서의 PDF 변환을 통합한 Streamlit 기반 웹 애플리케이션입니다.

### 주요 기능

1. **📄 문서 오타 검수**
   - Word/PDF 파일 업로드
   - OpenAI GPT를 활용한 AI 기반 오타 및 문법 검수
   - 실시간 하이라이팅으로 오류 표시
   - 수정 제안 및 이유 제공
   - 섹션별 상세한 오류 리포트

2. **🔄 PDF 일괄 변환**
   - Word(.docx, .doc) 및 PowerPoint(.pptx, .ppt) 파일을 PDF로 일괄 변환
   - Linux 환경에서 LibreOffice를 활용한 변환

## 🚀 설치 방법

### 사전 요구사항

- Python 3.8 이상
- OpenAI API Key (오타 검수 기능 사용 시)
- LibreOffice (PDF 변환 기능 사용 시, Linux 환경)

### 설치 단계

1. 저장소 클론
```bash
git clone <repository-url>
cd AI-agent/Committee-agent
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. NLTK 데이터 다운로드 (최초 실행 시 자동)
```bash
python -c "import nltk; nltk.download('punkt')"
```

5. PDF 변환 기능을 사용하려면 LibreOffice 설치 (Linux)
```bash
sudo apt-get update
sudo apt-get install libreoffice
```

## 💻 사용 방법

### 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저에서 자동으로 `http://localhost:8501`이 열립니다.

### 오타 검수 사용법

1. **탭 1: 📄 문서 오타 검수** 선택
2. OpenAI API Key 입력
3. Word 또는 PDF 파일 업로드
4. 왼쪽 패널에서 문서 내용 미리보기
5. "오타 검수 시작" 버튼 클릭
6. 오른쪽 패널에서 AI 검수 결과 확인
   - 오타가 발견된 문장은 빨간색으로 하이라이팅
   - 섹션별로 상세한 수정 제안 및 이유 표시

### PDF 변환 사용법

1. **탭 2: 🔄 PDF 일괄 변환** 선택
2. 변환할 파일이 있는 폴더 경로 입력
3. "일괄 변환 시작" 버튼 클릭
4. 변환된 PDF는 `pdf_output` 폴더에 저장

## 📁 프로젝트 구조

```
Committee-agent/
├── app.py                      # 메인 Streamlit 애플리케이션
├── read_docx_util.py          # Word 문서 읽기 유틸리티
├── highlighting.py            # 오타 하이라이팅 처리
├── pdf_converter.py           # PDF 변환 유틸리티
├── requirements.txt           # Python 의존성
└── README.md                  # 프로젝트 문서
```

## 🔧 모듈 설명

### app.py
메인 애플리케이션 파일로, Streamlit UI와 전체 워크플로우를 관리합니다.

### read_docx_util.py
UnstructuredWordDocumentLoader를 사용하여 Word 문서를 섹션별로 파싱합니다.
- 볼드체 텍스트를 섹션 제목으로 인식
- 표(Table) 구조 보존
- 콘텐츠를 섹션별로 그룹화

### highlighting.py
AI 분석 결과를 바탕으로 원본 텍스트에서 오류를 찾아 하이라이팅합니다.
- JSON 형식의 오류 목록 파싱
- HTML 스타일로 오류 강조
- 공백/줄바꿈을 고려한 유연한 매칭

### pdf_converter.py
LibreOffice를 사용하여 Office 문서를 PDF로 변환합니다.
- 일괄 변환 지원
- 진행 상황 실시간 업데이트
- 오류 처리 및 로깅

## 🎨 UI 구성

### 탭 1: 문서 오타 검수

**왼쪽 패널**
- API Key 입력
- 파일 업로드
- 문서 미리보기 (오류 하이라이팅 포함)

**오른쪽 패널**
- 검수 시작 버튼
- AI 수정 제안 요약
- 섹션별 상세 오류 리포트
  - 원본 문장 (취소선 + 빨간색 배경)
  - 수정 제안 (녹색 배경)
  - 수정 이유 설명

### 탭 2: PDF 일괄 변환
- 폴더 경로 입력
- 변환 진행 상황
- 성공/실패 로그

## ⚙️ 설정

### OpenAI API 설정
오타 검수 기능은 OpenAI의 GPT 모델을 사용합니다. 사용하려면:
1. [OpenAI Platform](https://platform.openai.com/)에서 API Key 발급
2. 애플리케이션 UI에서 API Key 입력

### GPT 모델 변경
`app.py`의 `get_proofreading_chain` 함수에서 모델 변경 가능:
```python
llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=api_key)
```

## 🐛 알려진 이슈

1. **PDF 변환 (Linux only)**: Windows/Mac에서는 LibreOffice 명령어 경로가 다를 수 있습니다.
2. **대용량 파일**: 매우 큰 문서는 처리 시간이 오래 걸릴 수 있습니다.
3. **API 비용**: OpenAI API 사용량에 따라 비용이 발생합니다.

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🤝 기여

버그 리포트, 기능 제안, PR을 환영합니다!

## 📧 문의

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.
