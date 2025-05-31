import argparse
from llm_handler import handle_request
from utils import pandas_to_sql
from settings import get_settings


settings = get_settings()


def main() -> None:
    parser = argparse.ArgumentParser(description="xinda test task")

    parser.add_argument(
        "--is_load_table", help="загрузить таблицу в БД", action="store_true"
    )
    parser.add_argument(
        "--ask",
        help="Задать вопрос на естественном языке для анализа",
        type=str,
    )
    parser.add_argument(
        "--verbose",
        help="Показать подробную информацию (SQL, результаты выполнения)",
        action="store_true",
    )

    args = parser.parse_args()

    if args.is_load_table:
        pandas_to_sql(settings.CSV_FILE_PATH, settings.SQLITE_DB, settings.SQLITE_TABLE)

    if args.ask:
        handle_request(args.ask, verbose=args.verbose)


if __name__ == "__main__":
    main()
