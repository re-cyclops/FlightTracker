"""tests for utilities.datenow debug overrides.

complements test_debug_date.py (which covers the core DEBUG_DATE and
DEBUG_TIME paths); these focus on parse edges not covered there.
"""
import sys
import types
from datetime import datetime

from utilities.datenow import get_now


def _fake_config(monkeypatch, **attrs):
    fake = types.ModuleType("config")
    for key, value in attrs.items():
        setattr(fake, key, value)
    monkeypatch.setitem(sys.modules, "config", fake)


class TestDebugOverrideEdges:
    def test_single_digit_debug_time_parses(self, monkeypatch):
        # given a debug time without zero padding
        _fake_config(monkeypatch, DEBUG_TIME="7:5")

        # when getting now
        result = get_now()

        # then the hour and minute are applied
        assert (result.hour, result.minute) == (7, 5)

    def test_out_of_range_minute_falls_back_to_real_time(self, monkeypatch):
        # given a debug time with an invalid minute
        _fake_config(monkeypatch, DEBUG_TIME="10:99")

        # when getting now
        result = get_now()

        # then the real time is kept
        assert abs(result.timestamp() - datetime.now().timestamp()) < 1

    def test_invalid_debug_time_keeps_valid_debug_date(self, monkeypatch):
        # given a valid debug date alongside a broken debug time
        _fake_config(monkeypatch, DEBUG_DATE="12-25", DEBUG_TIME="nope")

        # when getting now
        result = get_now()

        # then the date override still applies
        assert (result.month, result.day) == (12, 25)

    def test_non_string_debug_date_falls_back_to_real_date(self, monkeypatch):
        # given a debug date of the wrong type
        _fake_config(monkeypatch, DEBUG_DATE=1231)

        # when getting now
        result = get_now()

        # then the real date is kept
        assert abs(result.timestamp() - datetime.now().timestamp()) < 1
