from unittest.mock import MagicMock, patch
import pytest
from nvibrant_tui.backend import _MAX_DISPLAYS, _PATTERN, apply

SAMPLE_OUTPUT = (
    "• (0, HDMI1) • Vibrance set to 512 • Success\n"
    "• (1, DP1) • No monitor detected • None\n"
    "• (2, DVI1) • Driver error • Failed\n"
)


@pytest.fixture(autouse=True)
def _clear_binary_cache():
    from nvibrant_tui.backend import _binary

    _binary.cache_clear()
    yield
    _binary.cache_clear()


def _mock_run(stdout="", returncode=0):
    r = MagicMock()
    r.stdout = stdout
    r.returncode = returncode
    return r


class TestPattern:
    def test_parses_all_displays(self):
        assert len(list(_PATTERN.finditer(SAMPLE_OUTPUT))) == 3

    def test_success_groups(self):
        m = list(_PATTERN.finditer(SAMPLE_OUTPUT))[0]
        assert (m.group(1), m.group(2), m.group(3)) == ("0", "HDMI1", "Success")

    def test_none_status(self):
        assert list(_PATTERN.finditer(SAMPLE_OUTPUT))[1].group(3) == "None"

    def test_failed_status(self):
        assert list(_PATTERN.finditer(SAMPLE_OUTPUT))[2].group(3) == "Failed"

    def test_empty_output(self):
        assert list(_PATTERN.finditer("")) == []

    def test_extra_whitespace(self):
        out = "•   (3,  DP2  )  •  some description  •  Success"
        m = list(_PATTERN.finditer(out))
        assert len(m) == 1
        assert m[0].group(2).strip() == "DP2"
        assert m[0].group(3) == "Success"


class TestApply:
    def _run(self, stdout=SAMPLE_OUTPUT, returncode=0, values=None):
        with (
            patch("nvibrant_tui.backend.subprocess.run", return_value=_mock_run(stdout, returncode)),
            patch("nvibrant_tui.backend._binary", return_value="/usr/bin/nvibrant"),
        ):
            return apply(values if values is not None else [512, 0, 0])

    def test_success_flag(self):
        _, ok = self._run()
        assert ok is True

    def test_failure_flag(self):
        _, ok = self._run(returncode=1)
        assert ok is False

    def test_active_only_on_success(self):
        displays, _ = self._run()
        by_index = {d.index: d for d in displays}
        assert by_index[0].active is True
        assert by_index[1].active is False  # None
        assert by_index[2].active is False  # Failed

    def test_empty_output_returns_no_displays(self):
        displays, _ = self._run(stdout="")
        assert displays == []

    def test_detection_mode_passes_max_displays_zeros(self):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return _mock_run()

        with (
            patch("nvibrant_tui.backend.subprocess.run", side_effect=fake_run),
            patch("nvibrant_tui.backend._binary", return_value="/usr/bin/nvibrant"),
        ):
            apply(None)

        args = captured["cmd"][1:]
        assert args == ["0"] * _MAX_DISPLAYS
