import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache

import nvibrant


@dataclass
class Display:
    index: int
    port_type: str
    active: bool  # True = port has a monitor and vibrance was set successfully


_PATTERN = re.compile(r"•\s*\((\d+),\s*(\w+)\s*\)\s*•[^•]+•\s*(Success|None|Failed)")
_MAX_DISPLAYS = 16  # covers most multi-monitor setups


@lru_cache(maxsize=1)
def _binary() -> str:
    return str(nvibrant.get_best()[1])


def apply(values: list[int] | None = None) -> tuple[list[Display], bool]:
    args = [str(v) for v in values] if values is not None else ["0"] * _MAX_DISPLAYS
    result = subprocess.run([_binary(), *args], capture_output=True, text=True, timeout=10)
    displays = [
        Display(int(m.group(1)), m.group(2).strip(), m.group(3) == "Success") for m in _PATTERN.finditer(result.stdout)
    ]
    return displays, result.returncode == 0
