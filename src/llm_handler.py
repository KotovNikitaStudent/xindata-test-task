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


def ask_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.LLM_TEMPERATURE,
        seed=settings.LLM_SEED,
    )
    return response.choices[0].message.content


def handle_request(question: str, verbose: bool = False) -> None:
    table_structure = get_table_structure(settings.SQLITE_DB)

    categorical, numerical = analyze_columns(settings.SQLITE_DB, settings.SQLITE_TABLE)

    prompt = get_query_prompt.format(
        table_name=settings.SQLITE_TABLE,
        columns=", ".join(table_structure[settings.SQLITE_TABLE]),
        question=question,
        categorical="".join(
            [f"{col} - {', '.join(values)}\n" for col, values in categorical.items()]
        ),
        numerical=", ".join(numerical),
    )

    sql_code = ask_llm(prompt).strip("```sql").strip("```")

    result_df = execute_sql_query(settings.SQLITE_DB, sql_code)

    if verbose:
        print("\n🔍 Сгенерированный SQL-запрос:")
        print(sql_code)
        print("\n📊 Результат выполнения запроса:")
        print(result_df.to_string(index=False))

    explanation = explanation_prompt.format(
        sql_code=sql_code,
        result=result_df.to_markdown(index=False),
        question=question,
    )

    answer = ask_llm(explanation)

    print("\n💬 Ответ:")
    print(answer)
