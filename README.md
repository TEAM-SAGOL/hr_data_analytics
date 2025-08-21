HR 응답 분석 대시보드
💡 프로젝트 소개
이 프로젝트는 Streamlit을 활용하여 개발된 HR 응답 분석 대시보드입니다. Excel 파일로 된 정성적 데이터를 업로드하면 AI 기반 분석 파이프라인이 자동으로 키워드 추출, 감정 분석, 내용 요약 등의 작업을 수행하고, 그 결과를 시각화하여 보여줍니다. 분석 결과는 자동으로 폴더별로 저장되며, 대시보드에서 손쉽게 탐색할 수 있습니다.

✨ 주요 기능
엑셀 파일 업로드: .xlsx, .xls 형식의 데이터를 불러와 분석을 시작합니다.

AI 기반 데이터 전처리: GPT가 질문 컬럼을 자동으로 탐지하고, 무의미한 응답을 제거하여 데이터를 정제합니다.

통합 분석 파이프라인: 키워드 분석, 감정 분석, GPT 요약 과정을 효율적으로 처리합니다.

분석 결과 시각화: 워드클라우드, 막대그래프, 파이 차트 등 다양한 시각 자료를 생성합니다.

결과 파일 자동 저장: 분석 결과를 CSV 및 PNG 이미지 파일로 저장하며, 대상자별 폴더로 자동 분류됩니다.

결과 탐색 기능: 저장된 분석 결과를 대시보드 내에서 직접 탐색하고 확인할 수 있습니다.

🚀 시작하기
1. 프로젝트 다운로드
Git을 사용하여 프로젝트 저장소를 로컬 컴퓨터에 복제합니다.

Bash

git clone https://github.com/TEAM-SAGOL/hr_data_analytics.git
cd hr_data_analytics
2. 가상 환경 설정 및 라이브러리 설치
Python 가상 환경을 설정하고, 필요한 라이브러리를 requirements.txt 파일을 통해 한 번에 설치합니다.

Bash

# 가상 환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows

# requirements.txt 파일 생성
pip freeze > requirements.txt

# requirements.txt에 포함될 내용 (예시)
# streamlit>=1.20.0
# pandas
# matplotlib
# plotly
# seaborn
# openai
# langchain
# langchain-openai
# transformers
# wordcloud
# kaleido
# openpyxl
# ...

# 라이브러리 일괄 설치
pip install -r requirements.txt
3. OpenAI API 키 설정
보안을 위해 API 키는 코드에 직접 입력하지 않고 secrets.toml 파일을 통해 관리합니다.

프로젝트의 루트 폴더에 .streamlit 폴더를 생성합니다.

.streamlit 폴더 안에 secrets.toml 파일을 생성합니다.

secrets.toml 파일에 아래와 같이 API 키를 입력합니다.

Ini, TOML

[openai_section]
api_key = "여기에_실제_OpenAI_API_키를_붙여넣으세요"
Git 저장소에 API 키 파일이 실수로 업로드되지 않도록 .gitignore 파일을 생성하고 아래 내용을 추가합니다.

# Git에서 제외할 파일 및 폴더
.streamlit/secrets.toml
.venv/
📝 사용 방법
프로그램 실행
터미널에서 가상 환경이 활성화된 상태로 다음 명령어를 입력합니다.

Bash

streamlit run app.py
🏠 홈 페이지 (분석 시작)

데이터 업로드: '📂 엑셀 파일 업로드' 버튼을 클릭하여 분석할 파일을 선택합니다.

ID 컬럼 선택: 응답자를 구분하는 ID 컬럼을 선택합니다.

분석 모드 선택: '전체 대상자 분석' 또는 '특정 대상자 분석'을 선택합니다.

분석 시작: '분석 시작' 버튼을 클릭하면 분석이 시작됩니다.

📊 분석 페이지 (결과 확인)

폴더 선택: '분석 결과 폴더를 선택하세요' 드롭다운 메뉴에서 저장된 결과 폴더를 선택합니다.

대상자 선택: '분석 대상자 폴더를 선택하세요'에서 특정 대상자를 선택합니다.

결과 확인: 선택한 폴더에 있는 CSV, PNG 파일의 내용을 화면에서 바로 확인할 수 있습니다.

📂 프로젝트 구조
hr_data_analytics/
├── app.py
├── .gitignore
├── requirements.txt
├── .streamlit/
│   └── secrets.toml
└── modules/
    ├── analysis/
    │   ├── categorize.py
    │   ├── sentiment_module.py
    │   └── summary_module.py
    ├── long_format_converter.py
    ├── make_longformat.py
    ├── question_detector.py
    └── analysis_pipeline.py

❓ 문제 해결
API 키 오류: KeyError가 발생하면, secrets.toml 파일의 섹션 이름([openai_section])과 API 키가 정확한지 확인하세요.

폰트 오류: 그래프에서 글씨가 네모(□)로 깨져 보이면, app.py의 폰트 설정이 시스템에 설치된 폰트와 일치하는지 확인하세요. (예: AppleGothic 또는 Malgun Gothic)

모듈 오류: ModuleNotFoundError가 발생하면 requirements.txt에 해당 패키지가 포함되어 있는지 확인하고 pip install -r requirements.txt 명령어로 다시 설치하세요.