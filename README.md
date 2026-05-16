# nvibrant-tui

[![CI](https://github.com/enrialonso/nvibrant-tui/actions/workflows/ci.yml/badge.svg)](https://github.com/enrialonso/nvibrant-tui/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/nvibrant-tui)](https://pypi.org/project/nvibrant-tui/)
[![Python](https://img.shields.io/pypi/pyversions/nvibrant-tui)](https://pypi.org/project/nvibrant-tui/)
[![License: GPL v3](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

**Control NVIDIA Digital Vibrance from your terminal — per display, with sliders, and persistent across reboots.**

No more commands on every login. Set it once, enable autostart, and forget about it.

![demo.gif](assets/demo.gif)

---

## Install

```sh
pipx install nvibrant-tui
```

Then run:

```sh
nvibrant-tui
```

Your displays show up as sliders. Drag them or use the keyboard, hit **Apply**, and your settings are saved. Next login they'll be right where you left them — or enable **Autostart** and they'll be applied automatically before you even open the TUI.

<details>
<summary>Using pip instead of pipx?</summary>

```sh
pip install nvibrant-tui
```

</details>

---

## Controls

| Key                      | Action                  |
|--------------------------|-------------------------|
| `←` / `→`               | ±1                      |
| `Shift+←` / `Shift+→`  | ±64                     |
| `0`                      | Reset this display to 0 |
| `Ctrl+S`                 | Apply                   |
| `a`                      | Toggle auto-apply       |
| `l`                      | Link all displays       |
| `b`                      | Toggle autostart        |
| `Ctrl+Q`                 | Quit                    |

**Auto-apply** pushes changes to the driver as you move the slider, with a short debounce so it doesn't spam it on every tick.

**Link all** ties all displays together so one slider moves them all — useful if you want a uniform look across monitors.

---

## How settings are saved

Values are written to `~/.config/nvibrant-tui/config.json` only after nvibrant confirms the apply succeeded. You'll never end up with a saved state that wasn't actually applied.

**Autostart** installs `~/.config/systemd/user/nvibrant.service` — a one-shot service that fires after your graphical session starts. If you update your GPU driver or reinstall nvibrant, toggle Autostart off and on again to regenerate it pointing to the new binary.

---

## Requirements

- NVIDIA GPU with a working driver
- Wayland session
- Python 3.10+
- systemd user session *(only needed for Autostart)*

---

## Development

```sh
git clone https://github.com/enrialonso/nvibrant-tui
cd nvibrant-tui
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/nvibrant-tui
```

```sh
.venv/bin/pytest
```

---

## License

GPL-3.0 — see [LICENSE](LICENSE).