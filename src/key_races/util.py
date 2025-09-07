import os
import time
from typing import Any, Dict


def expand_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        # Simple ${VAR} expansion
        if value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1]
            return os.getenv(env_key)
        return value
    if isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env_vars(v) for v in value]
    return value


def polite_sleep(delay_seconds: float):
    try:
        if delay_seconds and delay_seconds > 0:
            time.sleep(delay_seconds)
    except Exception:
        pass

