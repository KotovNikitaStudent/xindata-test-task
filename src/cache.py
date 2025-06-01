import os
import json
from functools import wraps
from typing import Callable

from settings import get_settings


settings = get_settings()


def cache_analysis(func: Callable[..., tuple[dict, list]]):
    @wraps(func)
    def wrapper(repo, table_name: str, *args, **kwargs) -> tuple[dict, list]:
        db_path = repo.db_path

        os.makedirs(settings.CACHE_DIR, exist_ok=True)
        safe_table = table_name.replace("/", "_").replace("\\", "_")
        filename = f"{safe_table}@{os.path.basename(db_path)}.json"
        path = os.path.join(settings.CACHE_DIR, filename)

        if os.path.exists(path):
            db_mtime = os.path.getmtime(db_path)
            cache_mtime = os.path.getmtime(path)
            if cache_mtime >= db_mtime:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("categorical", {}), data.get("numerical", [])

        result = func(repo, table_name, *args, **kwargs)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"categorical": result[0], "numerical": result[1]},
                f,
                indent=2,
                ensure_ascii=False,
            )

        return result

    return wrapper
