"""tests for display.callsigns_match."""
import sys
import types


def _install_rgbmatrix_stub():
    # the venv has no rgbmatrix and the emulator needs a gui, so stub the
    # module-level surface (Font/Color at import time) before display loads
    if "rgbmatrix" in sys.modules:
        return

    class _Font:
        def LoadFont(self, path):
            pass

    class _Color:
        def __init__(self, r=0, g=0, b=0):
            self.red, self.green, self.blue = r, g, b

    graphics = types.ModuleType("rgbmatrix.graphics")
    graphics.Font = _Font
    graphics.Color = _Color
    graphics.DrawText = lambda *args, **kwargs: 0
    graphics.DrawLine = lambda *args, **kwargs: None

    rgbmatrix = types.ModuleType("rgbmatrix")
    rgbmatrix.graphics = graphics
    rgbmatrix.RGBMatrix = type("RGBMatrix", (), {})
    rgbmatrix.RGBMatrixOptions = type("RGBMatrixOptions", (), {})

    sys.modules["rgbmatrix"] = rgbmatrix
    sys.modules["rgbmatrix.graphics"] = graphics


_install_rgbmatrix_stub()

from display import callsigns_match  # noqa: E402


def _flights(*callsigns):
    return [{"callsign": c} for c in callsigns]


class TestCallsignsMatch:
    def test_identical_callsign_sets_match(self):
        # given two flight lists with the same callsigns
        # when comparing
        # then they match
        assert callsigns_match(_flights("UAL1", "DAL2"), _flights("UAL1", "DAL2")) is True

    def test_different_callsign_sets_do_not_match(self):
        # given two flight lists with different callsigns
        # when comparing
        # then they do not match
        assert callsigns_match(_flights("UAL1"), _flights("DAL2")) is False

    def test_duplicate_callsigns_collapse_to_one(self):
        # given one list with a duplicated callsign
        # when comparing against a single occurrence
        # then the set comparison treats them as equal
        assert callsigns_match(_flights("UAL1", "UAL1"), _flights("UAL1")) is True

    def test_two_empty_lists_match(self):
        # given two empty flight lists
        # when comparing
        # then they match
        assert callsigns_match([], []) is True

    def test_empty_list_does_not_match_populated_list(self):
        # given one empty and one populated flight list
        # when comparing
        # then they do not match
        assert callsigns_match([], _flights("UAL1")) is False
