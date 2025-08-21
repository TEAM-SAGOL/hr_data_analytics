# modules/question_detector.py
from openai import OpenAI
import json
import streamlit as st
import re

def detect_question_columns(columns: list, section_name: str='openai') -> list:
    prompt = f"""
아래는 설문 데이터의 컬럼명 목록입니다.
이 중에서 응답자가 텍스트로 답변을 작성하는 질문 컬럼들을 모두 골라주세요.

포함해야 할 컬럼 유형:
- 주관식 서술 응답 (예: '하고 싶은 말', '아쉬운 점', '잘한 점')
- 긍정적/부정적 경험이나 의견을 묻는 질문
- 행동이나 모습에 대한 평가나 설명을 요구하는 질문

제외해야 할 컬럼 유형:
- ID나 식별자 컬럼
- 관계나 속성을 나타내는 컬럼 (예: '대상자와의 관계')

컬럼 목록:
{columns}

반드시 JSON 배열 형식으로만 응답하세요. 다른 설명 없이 오직 배열만 주세요.
예시: ["질문1", "질문2", "Q1"]
"""
    
    try:
        client = OpenAI(api_key=st.secrets[section_name]['api_key'])
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        
        # 디버깅: OpenAI 응답 확인
        st.write("OpenAI 응답:", content)
        
        # 마크다운 코드 블록 제거
        if content.startswith('```'):
            # ```json 또는 ``` 로 시작하는 경우
            lines = content.split('\n')
            # 첫 번째와 마지막 라인 제거 (``` 라인들)
            content = '\n'.join(lines[1:-1]).strip()
        
        # JSON 추출 (배열 형태만)
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        
        st.write("정제된 JSON:", content)
        
        # JSON 파싱 시도
        result = json.loads(content)
        st.write("파싱된 결과:", result)
        return result
        
    except json.JSONDecodeError as e:
        st.error(f"JSON 파싱 에러: {e}")
        st.write("원본 응답:", content)
        return []
    except Exception as e:
        st.error(f"OpenAI API 에러: {e}")
        return []