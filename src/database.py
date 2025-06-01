from abc import ABC, abstractmethod
import sqlite3
import pandas as pd
from pathlib import Path
from cache import cache_analysis
from settings import get_settings
from logger import get_logger


settings = get_settings()
logger = get_logger(__name__)


class AbstractRepository(ABC):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @abstractmethod
    def load_csv_to_sql(self, csv_path: str, table_name: str) -> None:
        raise NotImplementedError

    def execute_query(self, query: str) -> pd.DataFrame:
        raise NotImplementedError

    def get_table_structure(self) -> dict[str, dict[str]]:
        raise NotImplementedError

    def table_exists(self, table_name: str) -> bool:
        raise NotImplementedError

    def analyze_columns(self, table_name: str) -> tuple[dict[str, list], list[str]]:
        raise NotImplementedError


class SQLiteRepository(AbstractRepository):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def load_csv_to_sql(self, csv_path: str, table_name: str) -> None:
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file {csv_path} not found.")
        df = pd.read_csv(csv_path)
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql(table_name, conn, index=False, if_exists="replace")
        logger.info("DataFrame successfully written to SQLite.")

    def execute_query(self, query: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

    def get_table_structure(self) -> dict[str, dict[str]]:
        structure = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                structure[table] = [info[1] for info in cursor.fetchall()]
        return structure

    def table_exists(self, table_name: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            return cursor.fetchone() is not None

    @cache_analysis
    def analyze_columns(self, table_name: str) -> tuple[dict[str, list], list[str]]:
        categorical = {}
        numerical = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in cursor.fetchall()]

            for col in columns:
                cursor.execute(
                    f"SELECT typeof({col}), {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 1;"
                )
                result = cursor.fetchone()
                sample_type = result[0].upper() if result else "NULL"

                cursor.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table_name};")
                unique_count = cursor.fetchone()[0]

                if sample_type == "TEXT" or unique_count <= settings.CAT_THRESHOLD:
                    cursor.execute(
                        f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL;"
                    )
                    categories = sorted(str(row[0]) for row in cursor.fetchall())
                    categorical[col] = categories
                else:
                    numerical.append(col)

        return categorical, numerical
