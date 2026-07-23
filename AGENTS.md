# FlightTracker LED Panel

Personal fork of [ColinWaddell/FlightTracker](https://github.com/ColinWaddell/FlightTracker) for a gift LED panel.

## Project Documentation

**Obsidian doc:** `~/personal/Obsidian/001 projects/PERSONAL/flight tracker led panel.md`

**IMPORTANT:** Update the Obsidian doc as you work:
- Mark animation checkboxes when completed
- Add new learnings to relevant sections
- Update status if project phase changes
- Add dated entries to any "Review Notes" sections

## Hardware

- Raspberry Pi 3 B+
- Adafruit RGB Matrix Bonnet
- Waveshare 64x32 P3 LED Matrix (P3-6432-2121-16S)
- 5V 4A power supply (panel), 5V 2.5A (Pi)

## Key Flags

```bash
--led-gpio-mapping=adafruit-hat
--led-no-hardware-pulse
--led-slowdown-gpio=4
```

## Architecture

```
display/__init__.py    # Display class inherits all scenes via multiple inheritance
scenes/                # Each scene is a class with @Animator.KeyFrame.add() methods
  clock.py             # Time display (12-hour AM/PM)
  weather.py           # Temperature from OpenWeatherMap
  heartbeat.py         # Pulsing heart when no flights (custom)
  flightdetails.py     # Flight info display
  ...
utilities/
  animator.py          # Animation framework with KeyFrame decorator
  overhead.py          # FlightRadar24 API integration
setup/
  colours.py           # Color constants (RED, BLUE, WHITE, etc.)
  fonts.py             # BDF font references
  frames.py            # Frame timing constants
```

## Adding New Animations

1. Create `scenes/myscene.py`:
```python
from utilities.animator import Animator
from setup import colours, frames

class MyScene(object):
    def __init__(self):
        super().__init__()

    @Animator.KeyFrame.add(frames.PER_SECOND * 1)
    def my_animation(self, count):
        if len(self._data):  # don't show if flights overhead
            return

        # draw pixels
        self.canvas.SetPixel(x, y, r, g, b)
```

2. Add to `display/__init__.py`:
```python
from scenes.myscene import MyScene

class Display(
    ...
    MyScene,  # add before Animator
    Animator,
):
```

## Drawing Methods

```python
self.canvas.SetPixel(x, y, r, g, b)
graphics.DrawText(self.canvas, font, x, y, colour, text)
graphics.DrawLine(self.canvas, x1, y1, x2, y2, colour)
self.draw_square(x0, y0, x1, y1, colour)  # from Display class
```

## Local Development

```bash
# LED viewer (recommended) - interactive animation browser
source env/bin/activate
python led_viewer.py
# open http://localhost:5555

# test single animation
python test_animation.py heartbeat
python test_animation.py birthday --scenario=day-of --name=Taylor
```

## Deploy to Pi

```bash
git add . && git commit -m "message" && git push
# then SSH to Pi:
ssh pi@flightpi.local
cd ~/FlightTracker && git pull && sudo systemctl restart flighttracker
```

## Config

Key settings in `config.py`:
- `ZONE_HOME` - lat/long bounding box for flight detection
- `LOCATION_HOME` - [lat, long, altitude_km]
- `WEATHER_LOCATION` - city for weather API (format: `Brooklyn,NY,US`)
- `OPENWEATHER_API_KEY` - free key from openweathermap.org
- `BRIGHTNESS` - 0-100
- `TEMPERATURE_UNITS` - "imperial" or "metric"
- `WINDOW_BEARING` / `WINDOW_FOV` - compass direction and field of view
- `MY_NAME` / `PARTNER_NAME` - names for birthday display
- `QUIET_SCHEDULE` - weekday/weekend dim and off periods
- `QUIET_HOURS_HIDE_FLIGHTS` - hide flights during dim hours (default False)

## Notes

- Display is 64x32 pixels
- Scenes show when `len(self._data) == 0` (no flights)
- Use `count` parameter in keyframe methods for timing
- Frame rate: `frames.PER_SECOND` = 10fps (not 30)
- All idle scenes must yield during quiet hours via `should_display_be_dim()`
- All idle scenes must clear `_last_*_pixels` on every early-return path
- Quiet-hours ambient picks one random scene per night (not rotating)
