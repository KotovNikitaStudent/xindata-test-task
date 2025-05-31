from openai import OpenAI

from prompts.get_query import prompt as get_query_prompt
from prompts.get_explanation import prompt as explanation_prompt

from utils import (
    analyze_columns,
    get_table_structure,
    execute_sql_query,
    pandas_to_sql,
    table_exists,
)

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
    if not question.strip() or len(question.strip()) < 5:
        print(
            "[Ошибка] Вопрос слишком короткий или пустой. Пожалуйста, уточните формулировку."
        )
        return

    if not table_exists(settings.SQLITE_DB, settings.SQLITE_TABLE):
        print(f"[Ошибка] Таблица '{settings.SQLITE_TABLE}' не найдена в базе данных.")
        print("Чтобы загрузить данные, выполните:")
        print("   poetry run python scr/main.py --is_load_table")
        print("\nИли хотите, чтобы я загрузил таблицу автоматически? [y/N]")
        choice = input().strip().lower()

        if choice in ("y", "yes"):
            print("[INFO] Загружаю данные в БД...")
            pandas_to_sql(
                settings.CSV_FILE_PATH, settings.SQLITE_DB, settings.SQLITE_TABLE
            )
        else:
            print("Выход.")
            return

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

    sql_code = ask_llm(prompt).strip("```sql").strip("```").strip()

    if not sql_code.lower().startswith("select"):
        print("[Ошибка] Модель сгенерировала некорректный SQL-запрос:")
        print(sql_code)
        print("Попробуйте переформулировать вопрос.")
        return

    try:
        result_df = execute_sql_query(settings.SQLITE_DB, sql_code)
    except Exception as e:
        print(f"[Ошибка] Не удалось выполнить SQL-запрос:\n{e}")
        return

    if result_df.empty:
        print(
            "[INFO] SQL-запрос выполнен, но результат пуст. Возможно, нет данных, удовлетворяющих условию."
        )
        return

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

    try:
        answer = ask_llm(explanation).strip()
    except Exception as e:
        print(f"[Ошибка] Не удалось интерпретировать результат: {e}")
        return

    if not answer or any(
        keyword in answer.lower()
        for keyword in ["не удалось", "ошибка", "не могу", "непонятно"]
    ):
        print("[Предупреждение] Модель не смогла корректно интерпретировать результат.")
        return

    print("\n💬 Ответ:")
    print(answer)
