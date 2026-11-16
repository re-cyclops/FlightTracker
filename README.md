# Flight Tracker LED

A Raspberry Pi and 64x32 RGB LED matrix that shows the aircraft passing overhead. It is a fork of [Colin Waddell's FlightTracker](https://github.com/ColinWaddell/FlightTracker), licensed under GPL-3.0 and carried over here under the same license. I built this fork as a gift, so most of the changes are about how the panel behaves at night and what it shows when nothing is in the sky.

## What this fork adds

- Window filter: only aircraft inside a configured bearing and field of view are shown. `WINDOW_BEARING` and `WINDOW_FOV` in `config.py` set the view. Setting either to `None` turns the filter off.
- Quiet hours: `QUIET_SCHEDULE` sets separate weekday and weekend windows. A `dim` window lowers brightness (default 30). An `off` window blanks the panel and wins where the two overlap. With `QUIET_HOURS_HIDE_FLIGHTS` on, flight data is cleared and not fetched during dim hours. The older `QUIET_HOURS_START`, `QUIET_HOURS_END`, `QUIET_MODE` and `QUIET_BRIGHTNESS` settings still work when `QUIET_SCHEDULE` is not set.
- Stale feed warning: if no fetch has succeeded for 600 seconds (`STALE_AFTER_SECONDS`), a warning pixel lights up on the panel. A dead feed otherwise looks like a quiet sky. Before the first successful fetch, the clock starts at the first attempt. The warning is hidden during the off window.
- Scenes: `scenes/` holds 32 scene modules. Idle scenes such as rain, starfield, aurora, fireplace and heartbeat run when no flights are overhead. Seasonal scenes such as halloween, christmas, valentines and chanukah follow the `HOLIDAYS` switches. Birthday and anniversary scenes read the special dates in `config.py`.
- An emulator workflow for developing without the panel (see below).
- Unit tests and a CI workflow (see Tests).

## Hardware

| Component | Model | Link |
| --------- | ----- | ---- |
| Computer | Raspberry Pi 3 B+ | [Adafruit](https://www.adafruit.com/product/3775) |
| Bonnet | Adafruit RGB Matrix Bonnet | [Adafruit](https://www.adafruit.com/product/3211) |
| Display | Waveshare 64x32 P3 LED Matrix (P3-6432-2121-16S) | [Waveshare](https://www.waveshare.com/rgb-matrix-p3-64x32.htm) |
| Power | 5V 4A DC Power Supply | [Adafruit](https://www.adafruit.com/product/1466) |

These are the key flags for this panel and bonnet combination:

```bash
--led-gpio-mapping=adafruit-hat
--led-no-hardware-pulse
--led-slowdown-gpio=4
```

The [original repository](https://github.com/ColinWaddell/FlightTracker) has full installation steps for the Pi.

## Configuration

```bash
cp config.example.py config.py
nano config.py
```

`config.example.py` documents every option. Its settings fall into these groups:

- Location: `ZONE_HOME` (latitude and longitude box), `LOCATION_HOME`, `WEATHER_LOCATION`, `JOURNEY_CODE_SELECTED`
- Window view filter: `WINDOW_BEARING`, `WINDOW_FOV`
- Display: `BRIGHTNESS`, `GPIO_SLOWDOWN`, `MIN_ALTITUDE`, `TEMPERATURE_UNITS`, `JOURNEY_BLANK_FILLER`, `HAT_PWM_ENABLED`, `HARDWARE_PULSE`, `LED_RGB_SEQUENCE`, `IDLE_ANIMATIONS_ENABLED`
- API keys: `OPENWEATHER_API_KEY`
- Special dates: `MY_BIRTHDAY`, `MY_NAME`, `PARTNER_BIRTHDAY`, `PARTNER_NAME`, `ANNIVERSARY`, `OTHER_BIRTHDAYS`
- Holidays: `HOLIDAYS`, a dict of on and off switches
- Quiet hours: `QUIET_SCHEDULE`, `QUIET_HOURS_HIDE_FLIGHTS`, and the legacy settings
- Custom messages: `LOVE_MESSAGES`, `QUOTES`
- Debug: `DEBUG_DATE`, `DEBUG_TIME`

## Develop without the panel

The emulator uses [RGBMatrixEmulator](https://github.com/ty-porter/RGBMatrixEmulator) to draw the panel in a browser.

```bash
git clone https://github.com/re-cyclops/FlightTracker
cd FlightTracker
python3 -m venv env
source env/bin/activate
pip install -r requirements-dev.txt
cp config.example.py config.py
```

`requirements.txt` skips `RPi.GPIO` off the Pi through an environment marker, so the install works on a Mac.

```bash
python run_emulator.py                    # open http://localhost:8888
python led_viewer.py                      # serves a viewer on http://localhost:5555
python test_animation.py heartbeat        # also: clock, weather, date, aurora, fireplace
python test_animation.py birthday --scenario=day-of --name=Taylor
```

The scene names that `test_animation.py` accepts are the keys of its scene mapping. Edit files in `scenes/`, then restart the emulator to see the change.

## Tests

```bash
python -m pytest tests/
python test_debug_date.py
```

`tests/` holds `conftest.py` and four test files covering callsign matching, date handling, the overhead logic and quiet hours. `test_debug_date.py` sits at the root and runs in CI after pytest. CI also byte-compiles every tracked Python file. The workflow is in `.github/workflows/ci.yml`.

## How scenes are scheduled

Each scene is a mixin class, and `Display` in `display/__init__.py` combines them into one class. The animator in `utilities/animator.py` finds every method with a `KeyFrame` decorator by walking `dir(self)`, which returns names in sorted order. Each frame it runs those methods in that order, at the interval their decorator sets. That is why the final steps carry a `zzzz` prefix: `zzzz_quiet_blank` runs after all scene drawing, and `zzzzz_sync` swaps the canvas last. This ordering comes from the original project's design, and it is the first part I would change.
