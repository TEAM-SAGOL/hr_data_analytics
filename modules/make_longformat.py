# modules/make_longformat.py
from modules.long_format_converter import convert_to_long_format
from modules.question_detector import detect_question_columns

def make_longformat(df, id_column, use_llm=False, section_name="openai"):
    if use_llm:
        question_columns = detect_question_columns(
            [col for col in df.columns if col != id_column],
            section_name=section_name
        )
    else:
        question_columns = [col for col in df.columns if col != id_column]

    long_df = convert_to_long_format(df, id_column, question_columns)
    return long_df, question_columns