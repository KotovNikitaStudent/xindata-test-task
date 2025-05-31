from openai import OpenAI

from prompts.get_query import prompt as get_query_prompt
from prompts.get_explanation import prompt as explanation_prompt

from utils import analyze_columns, get_table_structure, execute_sql_query

from settings import get_settings


settings = get_settings()

client = OpenAI(
    base_url=settings.LLM_API_URL,
    api_key=settings.LLM_API_KEY,
)


def ask_llm(prompt: str):
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.LLM_TEMPERATURE,
    )
    return response.choices[0].message.content


def handle_request(question: str):
    table_structure = get_table_structure(settings.SQLITE_DB)
    
    categorical, numerical = analyze_columns(settings.SQLITE_DB, settings.SQLITE_TABLE)

    prompt = get_query_prompt.format(
        table_name=settings.SQLITE_TABLE,
        columns=", ".join(table_structure[settings.SQLITE_TABLE]),
        question=question,
        categorical="".join([f"{col} - {', '.join(values)}\n" for col, values in categorical.items()]),
        numerical=", ".join(numerical),
    )

    print(prompt)
    print("*" * 100)

    sql_code = ask_llm(prompt)

    sql_code = sql_code.strip("```sql").strip("```")

    print(sql_code)
    print("*" * 100)

    result = execute_sql_query(settings.SQLITE_DB, sql_code)

    print(result)
    print("*" * 100)

    prompt = explanation_prompt.format(
        sql_code=sql_code, result=result.to_markdown(index=False), question=question
    )

    answer = ask_llm(prompt)
    print(answer)


if __name__ == "__main__":
    question = "Какие есть категории фрилансеров и сколько их в каждой категории?"
    handle_request(question)
