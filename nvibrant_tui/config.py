import json
import os
import tempfile
from pathlib import Path

_PATH = Path.home() / ".config/nvibrant-tui/config.json"


def load() -> dict:
    try:
        if not _PATH.exists():
            return {}
        data = json.loads(_PATH.read_text())
        values = data.get("values")
        if values is not None and (not isinstance(values, list) or not all(isinstance(v, int) for v in values)):
            return {}
        return data
    except Exception:
        return {}


def save(data: dict) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=_PATH.parent, prefix=".nvibrant-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(data, indent=2))
        os.replace(tmp, _PATH)
    except Exception:
        os.unlink(tmp)
        raise
