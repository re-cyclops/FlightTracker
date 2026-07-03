"""tests for utilities.overhead pure filtering helpers."""
from types import SimpleNamespace

import pytest

from utilities import overhead


def _window(monkeypatch, bearing, fov):
    monkeypatch.setattr(overhead, "WINDOW_BEARING", bearing)
    monkeypatch.setattr(overhead, "WINDOW_FOV", fov)


class TestIsInWindowView:
    def test_wraparound_bearing_near_north_is_visible(self, monkeypatch):
        # given a window facing north and a flight bearing just west of north
        _window(monkeypatch, 0, 20)
        monkeypatch.setattr(overhead, "bearing_from_home", lambda flight, home: 359)

        # when checking visibility
        # then the 1 degree wraparound difference is inside the fov
        assert overhead.is_in_window_view(SimpleNamespace()) is True

    def test_bearing_exactly_on_fov_edge_is_visible(self, monkeypatch):
        # given a flight bearing exactly half the fov away
        _window(monkeypatch, 0, 20)
        monkeypatch.setattr(overhead, "bearing_from_home", lambda flight, home: 10)

        # when checking visibility
        # then the inclusive edge is inside the fov
        assert overhead.is_in_window_view(SimpleNamespace()) is True

    def test_bearing_just_outside_fov_is_hidden(self, monkeypatch):
        # given a flight bearing just past half the fov
        _window(monkeypatch, 0, 20)
        monkeypatch.setattr(overhead, "bearing_from_home", lambda flight, home: 11)

        # when checking visibility
        # then it is outside the fov
        assert overhead.is_in_window_view(SimpleNamespace()) is False

    def test_unconfigured_window_shows_everything(self, monkeypatch):
        # given no window configured
        _window(monkeypatch, None, None)

        # when checking visibility
        # then every flight is visible
        assert overhead.is_in_window_view(SimpleNamespace()) is True


class TestBearingFromHome:
    HOME = [40.0, -74.0, overhead.EARTH_RADIUS_KM]

    def test_flight_due_north_bears_zero(self):
        # given a flight directly north of home
        flight = SimpleNamespace(latitude=41.0, longitude=-74.0)

        # when computing the bearing
        # then it is north
        assert overhead.bearing_from_home(flight, self.HOME) == pytest.approx(0, abs=0.5)

    def test_flight_due_east_bears_ninety(self):
        # given a flight directly east of home
        flight = SimpleNamespace(latitude=40.0, longitude=-73.0)

        # when computing the bearing
        # then it is east
        assert overhead.bearing_from_home(flight, self.HOME) == pytest.approx(90, abs=1)

    def test_flight_without_position_bears_zero(self):
        # given a flight missing position attributes
        # when computing the bearing
        # then it falls back to zero instead of raising
        assert overhead.bearing_from_home(SimpleNamespace(), self.HOME) == 0


class TestIsInAltitudeBand:
    @pytest.fixture(autouse=True)
    def _band(self, monkeypatch):
        monkeypatch.setattr(overhead, "MIN_ALTITUDE", 1000)
        monkeypatch.setattr(overhead, "MAX_ALTITUDE", 10000)

    def test_altitude_inside_band_is_included(self):
        # given a flight between the bounds
        # when checking the band
        # then it is included
        assert overhead.is_in_altitude_band(SimpleNamespace(altitude=5000)) is True

    def test_altitude_at_min_bound_is_excluded(self):
        # given a flight exactly at the minimum
        # when checking the band
        # then the exclusive bound rejects it
        assert overhead.is_in_altitude_band(SimpleNamespace(altitude=1000)) is False

    def test_altitude_at_max_bound_is_excluded(self):
        # given a flight exactly at the maximum
        # when checking the band
        # then the exclusive bound rejects it
        assert overhead.is_in_altitude_band(SimpleNamespace(altitude=10000)) is False
