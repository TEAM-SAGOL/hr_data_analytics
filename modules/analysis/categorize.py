# modules/analysis/categorize.py
import json, re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.exceptions import OutputParserException
from wordcloud import WordCloud
import streamlit as st # st.progress를 위해 streamlit 임포트 추가
import time

# 1. 프롬프트 엔지니어링으로 키워드 추출 + 키워드 카테고리 분류 
keyword_schema = ResponseSchema(name='keywords', description='추출된 핵심 키워드 리스트')
keyword_parser = StructuredOutputParser.from_response_schemas([keyword_schema])
keyword_prompt = ChatPromptTemplate.from_template("""
                                         
    당신은 정성적 응답 데이터를 분석하는 전문가입니다.
    아래 응답 목록에서 **핵심 키워드 3~5개**를 식별하세요.
    {texts}
    JSON 예시: {{ "keywords": ["소통", "책임감", "문제해결"] }}
    
""")

category_schema = ResponseSchema(name='categorized', description='키워드별 카테고리 매핑')
category_parser = StructuredOutputParser.from_response_schemas([category_schema])
category_prompt = ChatPromptTemplate.from_template("""
                                                 
    아래 키워드를 주제별 카테고리로 분류하세요.
    {keywords}
    JSON 예시: [{{"keyword": "소통", "category": "커뮤니케이션"}}]
    
    지침:
    - 카테고리는 '커뮤니케이션', '업무태도', '역량', '제도 및 환경', '기타' 5개로 지정함
    - '커뮤니케이션'의 주요 사례는 '소통, 협업, 리더십, 조직문화 등'임
    - '업무태도'의 주요 사례는 '책임감, 성실, 열정, 적극 등'임
    - '역량'의 주요 사례는 '해결, 전문성, 능력, 이해도 등'임
    - '제도 및 환경'의 주요 사례는 '복지, 시스템, 근무환경, 조직문화, 교육 운영, 워라밸 등'임
    - '기타'는 위 네 가지에 명확히 분류되지 않는 의견, 제안, 단순 감정 표현, 모호한 응답 등을 포함함
    - JSON 리스트 형식으로 반환
    - 불필요한 설명 없이 JSON만 응답

    키워드 목록:
    {keywords}

    출력 예시:
    [
      {{ "keyword": "소통", "category": "커뮤니케이션}},
      {{ "keyword": "책임감", "category": "업무태도" }}
    ]
    
""")

# 🔹 2. 키워드 추출
def process_batch(batch, llm):
    messages = keyword_prompt.format_messages(texts=batch)
    response = llm.invoke(messages)
    raw = response.content

    try:
        return keyword_parser.parse(raw)["keywords"]
    except OutputParserException:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                return parsed.get("keywords", [])
            except:
                return [] 
        return []

def extract_keywords_parallel(texts, llm, chunk_size=5, max_workers=4):
    all_keywords = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, texts[i:i+chunk_size], llm)
                   for i in range(0, len(texts), chunk_size)]
        for f in as_completed(futures):
            all_keywords.extend(f.result())
    return all_keywords

# 3. 카테고리 분류
def categorize_keywords_batch(keywords, llm, batch_size=50):
    categorized = []
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i+batch_size]
        prompt_text = category_prompt.format_messages(
            keywords=json.dumps(batch, ensure_ascii=False))[0].content
        
        
        response = llm.invoke([HumanMessage(content=prompt_text)])
        raw = response.content

        try:
            parsed = category_parser.parse(raw)
            categorized.extend(parsed)
        except:
            match = re.search(r"\[.*\]", raw, flags=re.DOTALL)
            if match:
                try:
                    categorized.extend(json.loads(match.group(0)))
                except:
                    continue
    return categorized


# 4. 통합 함수 
def run_keyword_analysis(texts, llm):
    # 진행률 바를 표시할 컨테이너
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0, text="키워드 추출 중...")
    
    # 키워드 추출 부분
    all_keywords = []
    texts_chunks = [texts[i:i + 5] for i in range(0, len(texts), 5)]
    total_chunks = len(texts_chunks)
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_batch, chunk, llm): i for i, chunk in enumerate(texts_chunks)}
        
        chunk_count = 0
        for future in as_completed(futures):
            all_keywords.extend(future.result())
            chunk_count += 1
            progress_percent = int(chunk_count / total_chunks * 50) # 총 50% 비중
            progress_bar.progress(progress_percent, text=f"키워드 추출 중...")

    unique_keywords = sorted(set(all_keywords))

    # 카테고리 분류 부분
    total_batches = len(unique_keywords) // 50 + (1 if len(unique_keywords) % 50 != 0 else 0)
    batch_count = 0
    categorized = []
    
    for i in range(0, len(unique_keywords), 50):
        batch = unique_keywords[i:i+50]
        parsed_cat = categorize_keywords_batch(batch, llm)
        categorized.extend(parsed_cat)
        batch_count += 1
        progress_percent = int(50 + (batch_count / total_batches * 50)) # 나머지 50% 비중
        progress_bar.progress(progress_percent, text=f"카테고리 분류 중...")

    progress_bar.progress(100, text="분석 완료!")
    time.sleep(0.5)
    progress_placeholder.empty() # 진행률 바를 화면에서 제거

    df_kw = pd.DataFrame(all_keywords, columns=["keyword"])
    df_kw["category"] = df_kw["keyword"].map({item["keyword"]: item["category"] for item in categorized}).fillna("기타")
    freq = df_kw.groupby(["keyword", "category"]).size().reset_index(name="count")


    return freq, {item["keyword"]: item["category"] for item in categorized}

# 5. 워드클라우드 
def generate_wordcloud_from_freq(freq_df):
    
    # 빈 워드클라우드 반환
    if freq_df.empty or 'keyword' not in freq_df.columns or 'count' not in freq_df.columns: 
        print("⚠️ freq_df is empty or missing required columns.")
        return None

    freq_dict = pd.Series(freq_df['count'].values, index=freq_df['keyword']).to_dict()
    wc = WordCloud(width=800, height=400, background_color='white', font_path='/Library/Fonts/AppleGothic.ttf')
    return wc.generate_from_frequencies(freq_dict)