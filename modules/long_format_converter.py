# modules/long_format_converter.py
import pandas as pd
import re

def convert_to_long_format(df: pd.DataFrame, id_column: str, question_columns: list) -> pd.DataFrame:
    long_df = pd.melt(
        df,
        id_vars=[id_column],
        value_vars=question_columns,
        var_name='질문',
        value_name='응답'
    )
    
    # 🚨 수정된 부분: 무의미한 응답 행 삭제 및 특정 문자열 제거
    # '응답' 컬럼에서 공백이나 NaN 값을 가진 행을 제거합니다.
    long_df['응답'] = long_df['응답'].fillna('').astype(str).str.strip()

    # 특정 무의미한 문자열 리스트 정의
    meaningless_responses = ["-", "없습니다.", "없음", "해당 없음", "해당없음", "x", "X"]
    
    # 응답이 비어 있거나 무의미한 문자열과 일치하는 행을 제거
    long_df = long_df[~long_df['응답'].isin(meaningless_responses)].copy()
    long_df = long_df[long_df['응답'] != ''].copy()
    
    # 🚨 추가된 부분: 문장 길이가 10 단어 미만인 행을 제거합니다.
    # 단어를 공백으로 구분하여 개수를 세고, 10 미만인 경우 삭제
    long_df = long_df[long_df['응답'].str.split().str.len() >= 10].copy()

    # NaN을 빈 문자열로 먼저 처리한 후 문자열 변환
    long_df[id_column] = long_df[id_column].astype(str)
    long_df['질문'] = long_df['질문'].astype(str)
    
    # 데이터프레임이 비어있을 경우 인덱스 오류 방지
    if long_df.empty:
        return long_df
        
    sample_id = long_df[id_column].iloc[0]
    has_numbers = bool(re.search(r'\d+', sample_id))
    
    if has_numbers:
        # 숫자가 포함된 경우: 숫자 부분을 추출하여 정렬
        def extract_number(text):
            numbers = re.findall(r'\d+', str(text))
            return int(numbers[0]) if numbers else 0
        
        long_df['_sort_key'] = long_df[id_column].apply(extract_number)
        long_df = long_df.sort_values(['_sort_key', '질문']).reset_index(drop=True)
        long_df = long_df.drop('_sort_key', axis=1)
    else:
        # 숫자가 없는 경우: 문자열 그대로 정렬
        long_df = long_df.sort_values([id_column, '질문']).reset_index(drop=True)
    
    return long_df