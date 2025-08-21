# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from matplotlib.ticker import MaxNLocator
import seaborn as sns
import openai
import sys
import os
import io
from datetime import datetime

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.analysis.categorize import run_keyword_analysis, generate_wordcloud_from_freq
from modules.analysis.summary_module import generate_summary_with_gpt
from modules.analysis.sentiment_module import (
    analyze_sentiment_with_finbert,
    refine_neutral_keywords_with_gpt,
    merge_sentiment_results,
    summarize_sentiment_by_category
)
from modules.analysis_pipeline import AnalysisPipeline
from langchain_openai import ChatOpenAI
from modules.question_detector import detect_question_columns
from modules.make_longformat import make_longformat

# 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 기본 설정
st.set_page_config(page_title="HR 응답 분석", layout="wide")

# GPT 모델 정의
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=st.secrets["openai_section"]["api_key"]
)

# 페이지 선택
menu = st.sidebar.selectbox("페이지 선택", ["🏠 홈", "📊 분석", "⚙️ 설정"])

# 홈 페이지
if menu == "🏠 홈":
    st.title("💼 HR 응답 분석 대시보드")
    
    # 1. 파일 업로드
    uploaded = st.file_uploader("📂 엑셀 파일 업로드", type=["xlsx", "xls"])
    
    # 2. 분석 시작
    if uploaded:
        df = pd.read_excel(uploaded)
        st.success("업로드 완료!")
        st.dataframe(df.head())
        
        st.write("---")

        analysis_mode = st.radio(
            "분석 모드를 선택하세요.",
            ("전체 대상자 분석", "특정 대상자 분석"),
            horizontal=True
        )
        
        id_col = st.selectbox("ID 컬럼을 선택하세요.", df.columns.tolist())
        selected_subject = None
        if analysis_mode == "특정 대상자 분석":
            if id_col:
                subject_list = df[id_col].dropna().unique().tolist()
                selected_subject = st.selectbox("분석할 대상자를 선택하세요.", subject_list)

        with st.form("analysis_form"):
            st.subheader("💡 분석을 위한 추가 정보 입력")
            user_prompt = st.text_area(
                "이 데이터는 무엇에 대한 데이터인가요? (예: '직원 만족도 설문조사', '팀 동료 평가 데이터')",
                key="user_prompt"
            )
            use_llm = st.checkbox("GPT가 자동으로 질문 컬럼을 찾아내도록 하기", value=True)
            submitted = st.form_submit_button("분석 시작")

        if submitted:
            if not user_prompt.strip():
                st.error("데이터에 대한 설명을 입력해주세요.")
            else:
                # 🚨 수정된 부분: 분석과 저장을 하나의 루프에서 처리
                
                # GPT가 질문 컬럼을 탐지
                with st.spinner("✨ 데이터 전처리 중..."):
                    question_cols = []
                    if use_llm:
                        st.info("AI가 질문 컬럼을 탐지하고 있습니다...")
                        question_cols = detect_question_columns(df.columns.tolist(), section_name="openai_section")
                        if not question_cols:
                            st.warning("GPT가 질문 컬럼을 찾지 못했습니다. 전체 컬럼을 분석 대상으로 지정합니다.")
                            question_cols = [col for col in df.columns if col != id_col]
                    else:
                        question_cols = [col for col in df.columns if col != id_col]
                    st.success(f"✔️ 분석 대상 컬럼: {question_cols}")
                
                # 분석 대상자 리스트 정의
                if analysis_mode == "특정 대상자 분석" and selected_subject:
                    subjects_to_analyze = [selected_subject]
                else:
                    subjects_to_analyze = df[id_col].dropna().unique().tolist()

                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name_prefix = uploaded.name.split('.')[0]
                base_dir = f"./{file_name_prefix}_{now}"
                analysis_dir = base_dir
                
                st.markdown("---")
                st.subheader("📦 분석 및 결과 저장")
                progress_bar = st.progress(0, text=f"분석 및 저장 진행 중 (0 / {len(subjects_to_analyze)})")

                with st.spinner("분석 및 파일을 저장하는 중입니다..."):
                    try:
                        for i, subject in enumerate(subjects_to_analyze):
                            st.info(f"✨ '{subject}'에 대한 분석을 시작합니다.")
                            
                            filtered_df = df[df[id_col] == subject].copy()
                            long_df, _ = make_longformat(filtered_df, id_column=id_col, use_llm=False)
                            long_df = long_df[long_df['질문'].isin(question_cols)]
                            
                            st.subheader("📁 Long Format 변환 결과")
                            st.dataframe(long_df)

                            texts = long_df['응답'].tolist()

                            if not texts:
                                st.warning(f"'{subject}'에 대한 분석할 텍스트가 없습니다. 다음 대상자로 넘어갑니다.")
                                progress_bar.progress((i + 1) / len(subjects_to_analyze), text=f"분석 및 저장 진행 중 ({i + 1} / {len(subjects_to_analyze)})")
                                continue

                            pipeline = AnalysisPipeline(llm, long_df)
                            if pipeline.run():
                                results = pipeline.get_results()

                                # 각 대상자별 폴더 생성
                                participant_dir = os.path.join(analysis_dir, subject)
                                os.makedirs(participant_dir, exist_ok=True)
                                st.info(f"분석 결과가 '{participant_dir}' 폴더에 저장됩니다.")
                                
                                # 시각화는 저장할 때 생성
                                fig_wc, ax_wc = plt.subplots()
                                wc = generate_wordcloud_from_freq(results['freq_df'])
                                if wc:
                                    ax_wc.imshow(wc, interpolation='bilinear')
                                    ax_wc.axis('off')
                                else:
                                    st.warning(f"'{subject}'에 대한 워드클라우드 생성 실패.")

                                fig_bar, ax_bar = plt.subplots()
                                freq_df = results['freq_df'].copy()
                                freq_df["count"] = freq_df["count"].astype(int)
                                freq_plot_df = freq_df.sort_values(by="count", ascending=False).head(20)
                                sns.barplot(data=freq_plot_df, y='keyword', x='count', hue='category', dodge=False, ax=ax_bar)
                                ax_bar.xaxis.set_major_locator(MaxNLocator(integer=True))
                                ax_bar.set_ylabel("키워드")
                                ax_bar.set_xlabel("count")
                                
                                overall_sentiment = results['sentiment_summary'].groupby('sentiment')['percentage'].sum().reset_index()
                                fig_pie = px.pie(
                                    overall_sentiment,
                                    names='sentiment',
                                    values='percentage',
                                    title='전체 감정 분포 (모든 키워드 기준)',
                                    color='sentiment',
                                    color_discrete_map={'긍정': '#63b2ee', '부정': '#ff9999', '중립': '#ffcc66'}
                                )
                                
                                # 파일 저장
                                results['freq_df'].to_csv(os.path.join(participant_dir, "keyword_freq.csv"), index=False)
                                results['updated_df'].to_csv(os.path.join(participant_dir, "sentiment.csv"), index=False)
                                if wc:
                                    fig_wc.savefig(os.path.join(participant_dir, "wordcloud.png"))
                                fig_pie.write_image(os.path.join(participant_dir, "piechart.png"))
                                fig_bar.savefig(os.path.join(participant_dir, "barchart.png"))
                                summary_df = pd.DataFrame([{'summary': results['summary_text']}])
                                summary_df.to_csv(os.path.join(participant_dir, "summary.csv"), index=False)
                                
                                st.success(f"✔️ '{subject}' 분석 및 저장 완료!")
                            progress_bar.progress((i + 1) / len(subjects_to_analyze), text=f"분석 및 저장 진행 중 ({i + 1} / {len(subjects_to_analyze)})")
                        
                        st.success("✔️ 모든 대상자 분석 및 저장이 성공적으로 완료되었습니다.")
                        st.warning("PDF 보고서 생성 기능은 현재 지원하지 않습니다.")
                        
                        # 저장 경로를 세션 상태에 저장
                        if 'last_analysis_path' not in st.session_state:
                            st.session_state.last_analysis_path = {}
                        st.session_state.last_analysis_path[os.path.basename(base_dir)] = analysis_dir
                        
                        # 분석 페이지로 이동
                        st.session_state['menu'] = '📊 분석'
                        st.rerun()

                    except Exception as e:
                        st.error(f"파일 저장 중 오류가 발생했습니다: {e}")

# 📊 분석 페이지
elif menu == "📊 분석":
    st.title("📊 분석 결과 확인")
    st.write("분석 결과를 폴더별로 탐색하고 확인하세요.")
    
    # 🚨 추가된 부분: 경로 입력 필드
    path_input = st.text_input(
        "확인할 분석 결과의 상위 폴더 경로를 입력하세요.",
        value="",
        placeholder="예: ./데이터가많은편_리더십,조직문화 다면진단 Data_2023_20250821_233332"
    )
    
    # 🚨 수정된 부분: 경로를 처리하는 로직
    current_path = None
    if path_input:
        if os.path.isdir(path_input):
            current_path = path_input
        else:
            st.error("⚠️ 유효하지 않은 경로입니다. 폴더가 존재하는지 확인해 주세요.")
    elif 'last_analysis_path' in st.session_state and st.session_state.last_analysis_path:
        selected_key = st.selectbox(
            "최근 분석 결과 폴더를 선택하거나, 위 경로를 직접 입력하세요.",
            list(st.session_state.last_analysis_path.keys())
        )
        if selected_key:
            current_path = st.session_state.last_analysis_path[selected_key]
    else:
        st.info("아직 저장된 분석 결과가 없습니다. '홈' 페이지에서 분석을 먼저 실행해 주세요.")

    if current_path:
        st.write(f"📂 현재 경로: `{current_path}`")
        
        # 폴더 내 파일 목록 가져오기
        files = [f for f in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, f))]
        sorted_files = sorted(files, key=lambda x: int(x.split('대상자')[1]))

        selected_file_name = st.selectbox(
            "분석 대상자 폴더를 선택하세요.",
            sorted_files
        )
        
        if selected_file_name:
            file_path = os.path.join(current_path, selected_file_name)
            
            inner_files = [f for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))]

            for file in inner_files:
                inner_file_path = os.path.join(file_path, file)
                file_extension = os.path.splitext(file)[1].lower()
                
                if file_extension in ['.csv', '.txt']:
                    st.subheader(f"📄 {file}")
                    df_or_text = pd.read_csv(inner_file_path) if file_extension == '.csv' else open(inner_file_path, 'r', encoding='utf-8').read()
                    st.code(df_or_text.to_csv(index=False) if file_extension == '.csv' else df_or_text)
                elif file_extension in ['.png', '.jpg', '.jpeg']:
                    st.subheader(f"🖼️ {file}")
                    st.image(inner_file_path)

# ⚙️ 설정 페이지
elif menu == "⚙️ 설정":
    st.title("⚙️ 설정")
    st.write("API 키 등 설정 가능")