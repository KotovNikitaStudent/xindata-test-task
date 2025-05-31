import os
import json
from functools import wraps
from typing import Callable

from settings import get_settings


settings = get_settings()


def cache_analysis(func: Callable[..., tuple[dict[str, list[str]], list[str]]]):
    @wraps(func)
    def wrapper(
        db_path: str, table_name: str, *args, **kwargs
    ) -> tuple[dict[str, list[str]], list[str]]:
        os.makedirs(settings.CACHE_DIR, exist_ok=True)
        safe_table_name = table_name.replace("/", "_").replace("\\", "_")
        cache_filename = f"{safe_table_name}@{os.path.basename(db_path)}.json"
        cache_path = os.path.join(settings.CACHE_DIR, cache_filename)

        if os.path.exists(cache_path):
            db_mtime = os.path.getmtime(db_path)
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime >= db_mtime:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return (
                        data.get("categorical", {}),
                        data.get("numerical", []),
                    )

        result = func(db_path, table_name, *args, **kwargs)

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {"categorical": result[0], "numerical": result[1]},
                f,
                indent=2,
                ensure_ascii=False,
            )

        return result

    return wrapper
