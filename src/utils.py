import sqlite3
import pandas as pd

from cache import cache_analysis


def get_csv_meta(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    return df


def pandas_to_sql(filename: str, db_name: str, tablename: str) -> None:
    df = pd.read_csv(filename)

    try:
        with sqlite3.connect(db_name) as conn:
            df.to_sql(tablename, conn, index=False, if_exists="replace")
        print("DataFrame successfully written to SQLite database.")
    except Exception as e:
        print(f"Error creating SQLite table: {e}")


def execute_sql_query(db_name: str, query: str) -> pd.DataFrame:
    try:
        with sqlite3.connect(db_name) as conn:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame()


def get_table_structure(db_path: str) -> dict[str, list[str]]:
    table_structure = {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [info[1] for info in cursor.fetchall()]
            table_structure[table] = columns

    return table_structure


@cache_analysis
def analyze_columns(
    db_path, table_name, cat_threshold=20
) -> tuple[dict[str, list[str]], list[str]]:
    categorical = {}
    numerical = []

    with sqlite3.connect(db_path) as conn:
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

            if sample_type == "TEXT" or unique_count <= cat_threshold:
                cursor.execute(
                    f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL;"
                )
                categories = sorted(str(row[0]) for row in cursor.fetchall())
                categorical[col] = categories
            else:
                numerical.append(col)

    return categorical, numerical
