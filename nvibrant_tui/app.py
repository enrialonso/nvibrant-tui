from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.css.query import NoMatches
from textual.events import MouseDown
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Label, LoadingIndicator, Switch
from textual import work

from nvibrant_tui import autostart, backend, config

_DEBOUNCE = 0.6


def _pct(value: int) -> str:
    if value >= 0:
        return f"{round(value * 100 / 1023)}%"
    return f"{round(value * 100 / 1024)}%"


class Slider(Widget, can_focus=True):
    DEFAULT_CSS = """
    Slider {
        height: 1;
        background: $surface-darken-2;
    }
    Slider:focus {
        background: $surface-darken-1;
        border-left: tall $accent;
    }
    """

    BINDINGS = [
        ("left", "step(-1)", "−1"),
        ("right", "step(1)", "+1"),
        ("shift+left", "step(-64)", "−64"),
        ("shift+right", "step(64)", "+64"),
        ("0", "reset", "Reset"),
    ]

    class Changed(Message):
        def __init__(self, slider: "Slider", value: int) -> None:
            self.slider = slider
            self.value = value
            super().__init__()

    def __init__(self, min_val: int, max_val: int, value: int, id: str | None = None) -> None:
        super().__init__(id=id)
        self._min = min_val
        self._max = max_val
        self._value = value if min_val <= value <= max_val else (min_val if value < min_val else max_val)

    @property
    def value(self) -> int:
        return self._value

    def _set_value(self, v: int) -> None:
        clamped = v if self._min <= v <= self._max else (self._min if v < self._min else self._max)
        if clamped != self._value:
            self._value = clamped
            self.refresh()
            self.post_message(self.Changed(self, self._value))

    def render(self) -> Text:
        w = self.size.width or 1
        ratio = (self._value - self._min) / (self._max - self._min)
        thumb = round(ratio * (w - 1))
        t = Text(no_wrap=True, overflow="crop")
        if thumb > 0:
            t.append("━" * thumb, style="bold cyan")
        t.append("◆", style="bold bright_cyan")
        remaining = w - thumb - 1
        if remaining > 0:
            t.append("─" * remaining, style="dim white")
        return t

    def action_step(self, delta: int) -> None:
        self._set_value(self._value + delta)

    def action_reset(self) -> None:
        self._set_value(0)

    def on_mouse_down(self, event: MouseDown) -> None:
        self.focus()  # keyboard shortcuts require focus after a click
        w = self.size.width or 1
        ratio = event.x / (w - 1) if w > 1 else 0.0
        ratio = 0.0 if ratio < 0.0 else (1.0 if ratio > 1.0 else ratio)
        self._set_value(round(self._min + ratio * (self._max - self._min)))


class DisplayRow(Widget):
    class Reset(Message):
        def __init__(self, row: "DisplayRow") -> None:
            self.row = row
            super().__init__()

    DEFAULT_CSS = """
    DisplayRow {
        height: auto;
        padding: 1 2;
        border-bottom: solid $surface-darken-1;
    }
    DisplayRow Horizontal {
        height: 1;
        margin-bottom: 1;
    }
    DisplayRow .port-label {
        width: 1fr;
    }
    DisplayRow .reset-btn {
        width: 6;
        min-width: 6;
        height: 1;
        padding: 0 1;
        background: transparent;
        color: $text-muted;
        border: none;
    }
    DisplayRow .reset-btn:hover {
        color: $accent;
        background: $surface;
    }
    DisplayRow .pct-label {
        width: 5;
        text-align: right;
        color: $text-muted;
    }
    DisplayRow .value-label {
        width: 6;
        text-align: right;
        color: $accent;
        margin-left: 1;
    }
    DisplayRow .value-label.dirty {
        color: $warning;
    }
    """

    def __init__(self, display: backend.Display, value: int) -> None:
        super().__init__()
        self.monitor = display
        self._saved_value = value

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"Display {self.monitor.index}  —  {self.monitor.port_type}", classes="port-label")
            yield Button("↺ [0]", classes="reset-btn")
            yield Label(_pct(self._saved_value), classes="pct-label")
            yield Label(str(self._saved_value), classes="value-label")
        yield Slider(min_val=-1024, max_val=1023, value=self._saved_value)

    def on_slider_changed(self, event: Slider.Changed) -> None:
        v = event.value
        self.query_one(".pct-label", Label).update(_pct(v))
        lbl = self.query_one(".value-label", Label)
        lbl.update(str(v))
        if v != self._saved_value:
            lbl.add_class("dirty")
        else:
            lbl.remove_class("dirty")
        # no stop() — bubbles to NvibrantApp

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.has_class("reset-btn"):
            self.query_one(Slider)._set_value(0)
            self.post_message(self.Reset(self))
            event.stop()

    def mark_saved(self, value: int) -> None:
        self._saved_value = value
        self.query_one(".value-label", Label).remove_class("dirty")

    @property
    def value(self) -> int:
        return self.query_one(Slider).value


class NvibrantApp(App):
    TITLE = "nvibrant-tui"
    BINDINGS = [
        ("ctrl+s", "apply", "Apply"),
        ("a", "toggle_auto_apply", "Auto-apply"),
        ("l", "toggle_link_all", "Link all"),
        ("b", "toggle_autostart", "Autostart"),
        ("ctrl+q", "quit", "Quit"),
    ]
    CSS = """
    Screen {
        align: center top;
    }
    #card {
        width: 100%;
        max-width: 100;
        min-width: 60;
        height: 100%;
        border: round $surface-lighten-1;
        background: $surface;
    }
    #displays {
        height: 1fr;
    }
    #bottom {
        height: 5;
        padding: 1 2;
        border-top: solid $surface-darken-1;
        align: left middle;
    }
    #apply {
        margin-right: 2;
    }
    #auto-apply-label, #link-label, #autostart-label {
        margin-right: 1;
    }
    #auto-apply, #link-all {
        margin-right: 3;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._debounce_timer = None
        self._linking = False
        self._systemd_available = autostart.is_available()

    def compose(self) -> ComposeResult:
        yield Header()
        with Widget(id="card"):
            yield ScrollableContainer(LoadingIndicator(), id="displays")
            with Horizontal(id="bottom"):
                yield Button("Apply [^S]", variant="primary", id="apply")
                yield Label("Auto-apply [a]", id="auto-apply-label")
                yield Switch(value=False, id="auto-apply")
                yield Label("Link all [l]", id="link-label")
                yield Switch(value=True, id="link-all")
                yield Label("Autostart [b]", id="autostart-label")
                yield Switch(
                    value=False,
                    id="autostart",
                    disabled=not self._systemd_available,
                    tooltip="" if self._systemd_available else "Requires systemd",
                )
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    @work(thread=True)
    def _load(self) -> None:
        cfg = config.load()
        saved = cfg.get("values")
        try:
            displays, _ = backend.apply(saved)
        except Exception as e:
            self.call_from_thread(self._show_error, str(e))
            return
        self.call_from_thread(self._populate, displays, saved)

    def _populate(self, displays: list[backend.Display], saved: list[int] | None) -> None:
        container = self.query_one("#displays", ScrollableContainer)
        container.remove_children()
        active = [d for d in displays if d.active]
        if not active:
            container.mount(Label("  No connected displays found.", markup=False))
            return
        for d in active:
            value = saved[d.index] if saved and d.index < len(saved) else 0
            container.mount(DisplayRow(d, value))

    def _show_error(self, message: str) -> None:
        container = self.query_one("#displays", ScrollableContainer)
        container.remove_children()
        container.mount(Label(f"  Error: {message}", markup=False))

    def _collect_values(self) -> list[int]:
        rows = list(self.query(DisplayRow))
        if not rows:
            return []
        max_idx = max(r.monitor.index for r in rows)
        values = [0] * (max_idx + 1)
        for row in rows:
            values[row.monitor.index] = row.value
        return values

    def _set_pending(self, pending: bool) -> None:
        try:
            self.query_one("#apply", Button).label = "Apply ● [^S]" if pending else "Apply [^S]"
        except NoMatches:
            pass

    def _schedule_auto_apply(self) -> None:
        self._set_pending(True)
        try:
            if not self.query_one("#auto-apply", Switch).value:
                return
        except NoMatches:
            return
        if self._debounce_timer is not None:
            self._debounce_timer.stop()
        self._debounce_timer = self.set_timer(_DEBOUNCE, self._debounced_apply)

    def on_slider_changed(self, event: Slider.Changed) -> None:
        if not self._linking:
            try:
                if self.query_one("#link-all", Switch).value:
                    self._linking = True
                    for row in self.query(DisplayRow):
                        s = row.query_one(Slider)
                        if s is not event.slider:
                            s._set_value(event.value)
                    self._linking = False
            except NoMatches:
                self._linking = False
        self._schedule_auto_apply()

    def on_display_row_reset(self, event: DisplayRow.Reset) -> None:
        try:
            if self.query_one("#link-all", Switch).value:
                for row in self.query(DisplayRow):
                    if row is not event.row:
                        row.query_one(Slider)._set_value(0)
        except NoMatches:
            pass
        self._schedule_auto_apply()

    def _debounced_apply(self) -> None:
        self._debounce_timer = None
        values = self._collect_values()
        if not values:  # empty list would reset all displays via nvibrant
            return
        do_autostart = self.query_one("#autostart", Switch).value
        self._apply(values, do_autostart, silent=True)

    def action_toggle_auto_apply(self) -> None:
        sw = self.query_one("#auto-apply", Switch)
        sw.value = not sw.value

    def action_toggle_link_all(self) -> None:
        sw = self.query_one("#link-all", Switch)
        sw.value = not sw.value

    def action_toggle_autostart(self) -> None:
        sw = self.query_one("#autostart", Switch)
        if not sw.disabled:
            sw.value = not sw.value

    def action_apply(self) -> None:
        values = self._collect_values()
        if not values:  # empty list would reset all displays via nvibrant
            return
        do_autostart = self.query_one("#autostart", Switch).value
        self._apply(values, do_autostart)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            self.action_apply()

    @work(thread=True)
    def _apply(self, values: list[int], do_autostart: bool, silent: bool = False) -> None:
        try:
            _, success = backend.apply(values)
        except Exception:
            self.call_from_thread(self._on_applied, values, False, False)
            return
        if success:
            config.save({"values": values})
            if do_autostart:
                autostart.enable(values)
        self.call_from_thread(self._on_applied, values, success, silent)

    def _on_applied(self, values: list[int], success: bool, silent: bool) -> None:
        self._set_pending(False)
        if success:
            for row in self.query(DisplayRow):
                if row.monitor.index < len(values):
                    row.mark_saved(values[row.monitor.index])
        if not silent or not success:
            self.notify(
                "Applied!" if success else "Failed to apply",
                severity="information" if success else "error",
            )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id != "autostart":
            return
        values = self._collect_values()
        self._toggle_autostart(event.value, values)

    @work(thread=True)
    def _toggle_autostart(self, enable: bool, values: list[int]) -> None:
        if enable and values:  # displays may not be loaded yet if switch toggled during startup
            autostart.enable(values)
        elif not enable:
            autostart.disable()
