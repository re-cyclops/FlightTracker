"""tests for utilities.quiethours pure logic."""
from datetime import datetime, time

from utilities import quiethours


class TestTimeInRange:
    def test_midnight_crossing_range_includes_time_before_midnight(self):
        # given a range that crosses midnight
        # when checking a time before midnight
        # then it is inside the range
        assert quiethours._time_in_range("22:00", "02:00", time(23, 0)) is True

    def test_midnight_crossing_range_includes_time_after_midnight(self):
        # given a range that crosses midnight
        # when checking a time after midnight but before the end
        # then it is inside the range
        assert quiethours._time_in_range("22:00", "02:00", time(1, 0)) is True

    def test_midnight_crossing_range_excludes_time_past_end(self):
        # given a range that crosses midnight
        # when checking a time after the end and before the start
        # then it is outside the range
        assert quiethours._time_in_range("22:00", "02:00", time(3, 0)) is False

    def test_normal_range_includes_time_inside(self):
        # given a same-day range
        # when checking a time inside it
        # then it is inside the range
        assert quiethours._time_in_range("09:00", "17:00", time(12, 0)) is True

    def test_normal_range_excludes_time_outside(self):
        # given a same-day range
        # when checking a time after the end
        # then it is outside the range
        assert quiethours._time_in_range("09:00", "17:00", time(18, 0)) is False

    def test_invalid_time_string_is_never_in_range(self):
        # given an unparseable start time
        # when checking any time
        # then the range never matches
        assert quiethours._time_in_range("banana", "17:00", time(12, 0)) is False


def _fixed_now(monkeypatch, hour, minute):
    # a wednesday, so weekday schedule applies
    fixed = datetime(2026, 1, 7, hour, minute)
    monkeypatch.setattr(quiethours, "get_now", lambda: fixed)


class TestGetQuietStatus:
    def test_off_takes_priority_over_dim_when_windows_overlap(self, monkeypatch):
        # given a weekday schedule where off and dim windows both cover 22:30
        schedule = {
            "weekday": {
                "off": {"start": "22:00", "end": "06:00"},
                "dim": {"start": "20:00", "end": "23:00", "brightness": 40},
            }
        }
        monkeypatch.setattr(quiethours, "_load_schedule", lambda: schedule)
        _fixed_now(monkeypatch, 22, 30)

        # when getting the quiet status
        status = quiethours.get_quiet_status()

        # then off wins over dim
        assert status["mode"] == "off"


class TestGetBrightness:
    def test_dim_mode_returns_configured_brightness(self, monkeypatch):
        # given a dim window covering the current time
        schedule = {
            "weekday": {"dim": {"start": "20:00", "end": "23:00", "brightness": 40}}
        }
        monkeypatch.setattr(quiethours, "_load_schedule", lambda: schedule)
        _fixed_now(monkeypatch, 21, 0)

        # when getting the brightness
        # then the configured dim brightness is returned
        assert quiethours.get_brightness() == 40

    def test_off_mode_returns_zero_brightness(self, monkeypatch):
        # given an off window covering the current time
        schedule = {"weekday": {"off": {"start": "22:00", "end": "06:00"}}}
        monkeypatch.setattr(quiethours, "_load_schedule", lambda: schedule)
        _fixed_now(monkeypatch, 23, 0)

        # when getting the brightness
        # then it is zero
        assert quiethours.get_brightness() == 0

    def test_no_config_returns_full_brightness(self, monkeypatch):
        # given no schedule and no legacy config
        monkeypatch.setattr(quiethours, "_load_schedule", lambda: None)
        monkeypatch.setattr(quiethours, "_load_legacy_config", lambda: None)

        # when getting the brightness
        # then it is full
        assert quiethours.get_brightness() == 100
