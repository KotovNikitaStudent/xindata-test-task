import argparse
import os
from database import SQLiteRepository
from llm import QueryHandler
from settings import get_settings
from logger import get_logger


settings = get_settings()
logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Data analysis CLI tool")
    parser.add_argument(
        "--load-table", action="store_true", help="Load CSV into SQLite"
    )
    parser.add_argument("--ask", type=str, help="Ask a natural language question")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    db_manager = SQLiteRepository(settings.SQLITE_DB)

    if args.load_table:
        if not os.path.exists(settings.CSV_FILE_PATH):
            logger.error(f"CSV file not found: {settings.CSV_FILE_PATH}")
            return
        db_manager.load_csv_to_sql(settings.CSV_FILE_PATH, settings.SQLITE_TABLE)

    if args.ask:
        processor = QueryHandler(db_manager)
        processor.handle_request(args.ask, verbose=args.verbose)


if __name__ == "__main__":
    main()
