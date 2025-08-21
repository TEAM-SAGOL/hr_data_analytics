# modules/analysis_pipeline.py
import streamlit as st
import pandas as pd
import time

from modules.analysis.categorize import run_keyword_analysis
from modules.analysis.summary_module import generate_summary_with_gpt
from modules.analysis.sentiment_module import (
    analyze_sentiment_with_finbert,
    refine_neutral_keywords_with_gpt,
    merge_sentiment_results,
    summarize_sentiment_by_category
)

class AnalysisPipeline:
    def __init__(self, llm, long_df):
        self.llm = llm
        self.long_df = long_df
        self.results = {}
        self.texts = long_df['응답'].tolist()

    def run(self):
        progress_bar = st.progress(0, text="분석 파이프라인 시작 중...")
        
        st.subheader("키워드 분석 중...")
        progress_bar_1 = st.progress(0, text="키워드 추출 및 카테고리 분류 중...")
        freq_df, categorized_df = run_keyword_analysis(self.texts, self.llm)
        self.results['freq_df'] = freq_df
        self.results['categorized_df'] = categorized_df
        progress_bar_1.progress(100)
        st.success("✔️ 키워드 분석 완료!")
        progress_bar.progress(0.33, text="키워드 분석 완료!")
        
        st.subheader("감정 분석 중...")
        with st.spinner("감정 분석 및 재분류 중..."):
            sentiment_df = analyze_sentiment_with_finbert(
                self.texts, 
                self.llm,
                self.results['freq_df'],
                self.results['categorized_df']
            )
            refined_df = refine_neutral_keywords_with_gpt(sentiment_df, self.llm)
            updated_df = merge_sentiment_results(sentiment_df, refined_df)
            sentiment_summary = summarize_sentiment_by_category(self.results['freq_df'], updated_df)
            self.results['updated_df'] = updated_df
            self.results['sentiment_summary'] = sentiment_summary
            st.success("✔️ 감정 분석 완료!")
            progress_bar.progress(0.66, text="감정 분석 완료!")

        st.subheader("GPT 요약 중...")
        with st.spinner("GPT가 응답을 요약 중입니다..."):
            summary_text = generate_summary_with_gpt(self.texts)
            self.results['summary_text'] = summary_text
            st.success("✔️ 요약 완료!")
            progress_bar.progress(1.0, text="요약 완료!")
            time.sleep(1)

        st.success("🎉 모든 분석이 완료되었습니다. 결과를 확인하세요.")
        return True

    def get_results(self):
        return self.results