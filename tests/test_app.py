from unittest.mock import patch
import pytest
from nvibrant_tui.app import NvibrantApp, _pct, DisplayRow, Slider
from nvibrant_tui.backend import Display

_DISPLAYS = [
    Display(index=0, port_type="HDMI1", active=True),
    Display(index=1, port_type="DP1", active=True),
]

_SAVED = [512, 256]


@pytest.fixture
def mock_env():
    with (
        patch("nvibrant_tui.backend.apply", return_value=(_DISPLAYS, True)),
        patch("nvibrant_tui.config.load", return_value={"values": _SAVED}),
        patch("nvibrant_tui.config.save"),
        patch("nvibrant_tui.autostart.is_available", return_value=False),
        patch("nvibrant_tui.autostart.is_enabled", return_value=False),
    ):
        yield


class TestPct:
    def test_zero(self):
        assert _pct(0) == "0%"

    def test_max(self):
        assert _pct(1023) == "100%"

    def test_negative(self):
        assert _pct(-1024) == "-100%"


class TestApplyInvariant:
    async def test_never_called_with_empty_list(self):
        """When no displays are mounted, Apply must abort — never send [] to backend."""
        apply_calls = []

        def track(values=None):
            apply_calls.append(values)
            return ([], True)  # no active displays → no DisplayRows → _collect_values() == []

        with (
            patch("nvibrant_tui.backend.apply", side_effect=track),
            patch("nvibrant_tui.config.load", return_value={}),
            patch("nvibrant_tui.config.save") as mock_save,
            patch("nvibrant_tui.autostart.is_available", return_value=False),
            patch("nvibrant_tui.autostart.is_enabled", return_value=False),
        ):

            async with NvibrantApp().run_test() as pilot:
                await pilot.pause(0.3)
                apply_calls.clear()  # discard the detection call from _load()

                await pilot.press("ctrl+s")
                await pilot.pause(0.1)

                assert [] not in apply_calls
                mock_save.assert_not_called()


class TestCollectValues:
    async def test_maps_display_indices_to_slider_values(self, mock_env):
        async with NvibrantApp().run_test() as pilot:
            await pilot.pause(0.3)

            values = pilot.app._collect_values()
            assert values[0] == _SAVED[0]
            assert values[1] == _SAVED[1]

    async def test_returns_empty_when_no_displays_mounted(self):
        with (
            patch("nvibrant_tui.backend.apply", return_value=([], True)),
            patch("nvibrant_tui.config.load", return_value={}),
            patch("nvibrant_tui.autostart.is_available", return_value=False),
            patch("nvibrant_tui.autostart.is_enabled", return_value=False),
        ):

            async with NvibrantApp().run_test() as pilot:
                await pilot.pause(0.3)
                assert pilot.app._collect_values() == []


class TestLinkAll:
    async def test_moving_one_slider_propagates_to_all(self, mock_env):
        async with NvibrantApp().run_test() as pilot:
            await pilot.pause(0.3)

            rows = list(pilot.app.query(DisplayRow))
            assert len(rows) == 2

            rows[0].query_one(Slider)._set_value(900)
            await pilot.pause(0.1)

            assert rows[1].query_one(Slider).value == 900
