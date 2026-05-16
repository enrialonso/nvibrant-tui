import os
import subprocess
from pathlib import Path

import nvibrant

_SERVICE_PATH = Path.home() / ".config/systemd/user/nvibrant.service"


def is_available() -> bool:
    xdg = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(xdg, "systemd", "private").exists()


def is_enabled() -> bool:
    return _SERVICE_PATH.exists()


def enable(values: list[int]) -> None:
    binary = nvibrant.get_best()[1]
    args = " ".join(str(v) for v in values)
    _SERVICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SERVICE_PATH.write_text(f"""\
[Unit]
Description=Apply nvibrant
After=graphical.target

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart={binary} {args}

[Install]
WantedBy=default.target
""")
    subprocess.run(["systemctl", "--user", "enable", "nvibrant.service"], check=False)


def disable() -> None:
    subprocess.run(["systemctl", "--user", "disable", "nvibrant.service"], check=False)
    if _SERVICE_PATH.exists():
        _SERVICE_PATH.unlink()
