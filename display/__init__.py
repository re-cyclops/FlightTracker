import sys

from setup import frames
from utilities.animator import Animator
from utilities.overhead import Overhead
from utilities.quiethours import should_display_be_dim, get_quiet_status

from scenes.weather import WeatherScene
from scenes.flightdetails import FlightDetailsScene
from scenes.journey import JourneyScene
from scenes.loadingpulse import LoadingPulseScene
try:
    from scenes.loadingled import LoadingLEDScene
except ImportError:
    LoadingLEDScene = LoadingPulseScene  # fallback on Mac
from scenes.clock import ClockScene
from scenes.planedetails import PlaneDetailsScene
from scenes.date import DateScene
from scenes.heartbeat import HeartbeatScene
from scenes.lovemessages import LoveMessagesScene
from scenes.starfield import StarfieldScene
from scenes.oceanwaves import OceanWavesScene
from scenes.fallingsnow import FallingSnowScene
from scenes.aurora import AuroraScene
from scenes.fireplace import FireplaceScene
from scenes.candlelight import CandlelightScene
from scenes.moonrise import MoonriseScene
from scenes.rain import RainScene
from scenes.birthday import BirthdayScene
from scenes.anniversary import AnniversaryScene
from scenes.timeofday import TimeOfDayScene
from scenes.valentines import ValentinesScene
from scenes.halloween import HalloweenScene
from scenes.chanukah import ChanukahScene
from scenes.newyear import NewYearScene
from scenes.christmas import ChristmasScene
from scenes.stpatricks import StPatricksScene
from scenes.easter import EasterScene
from scenes.independence import IndependenceScene
from scenes.thanksgiving import ThanksgivingScene
from scenes.chinesenewyear import ChineseNewYearScene
from scenes.planeintro import PlaneIntroScene

from rgbmatrix import graphics
from rgbmatrix import RGBMatrix, RGBMatrixOptions


def callsigns_match(flights_a, flights_b):
    get_callsigns = lambda flights: [f["callsign"] for f in flights]
    callsigns_a = set(get_callsigns(flights_a))
    callsigns_b = set(get_callsigns(flights_b))

    return callsigns_a == callsigns_b


try:
    # Attempt to load config data
    from config import (
        BRIGHTNESS,
        GPIO_SLOWDOWN,
        HAT_PWM_ENABLED
    )

except (ModuleNotFoundError, NameError):
    # If there's no config data
    BRIGHTNESS = 100
    GPIO_SLOWDOWN = 1
    HAT_PWM_ENABLED = True

try:
    # Attempt to load experimental config data
    from config import LOADING_LED_ENABLED

except (ModuleNotFoundError, NameError, ImportError):
    # If there's no experimental config data
    LOADING_LED_ENABLED = False

try:
    from config import LED_RGB_SEQUENCE
except (ModuleNotFoundError, NameError, ImportError):
    LED_RGB_SEQUENCE = "RGB"

try:
    from config import QUIET_HOURS_HIDE_FLIGHTS
except (ModuleNotFoundError, NameError, ImportError):
    QUIET_HOURS_HIDE_FLIGHTS = False


class Display(
    WeatherScene,
    PlaneIntroScene,
    FlightDetailsScene,
    JourneyScene,
    LoadingLEDScene if LOADING_LED_ENABLED else LoadingPulseScene,
    PlaneDetailsScene,
    ClockScene,
    DateScene,
    HeartbeatScene,
    LoveMessagesScene,
    StarfieldScene,
    OceanWavesScene,
    FallingSnowScene,
    AuroraScene,
    FireplaceScene,
    CandlelightScene,
    MoonriseScene,
    RainScene,
    BirthdayScene,
    AnniversaryScene,
    TimeOfDayScene,
    ValentinesScene,
    HalloweenScene,
    ChanukahScene,
    NewYearScene,
    ChristmasScene,
    StPatricksScene,
    EasterScene,
    IndependenceScene,
    ThanksgivingScene,
    ChineseNewYearScene,
    Animator,
):
    def __init__(self):
        # Setup Display
        options = RGBMatrixOptions()
        options.hardware_mapping = "adafruit-hat-pwm" if HAT_PWM_ENABLED else "adafruit-hat"
        options.rows = 32
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.row_address_type = 0
        options.multiplexing = 0
        options.pwm_bits = 7
        options.brightness = BRIGHTNESS
        options.pwm_lsb_nanoseconds = 130
        options.led_rgb_sequence = LED_RGB_SEQUENCE
        options.pixel_mapper_config = ""
        options.show_refresh_rate = 0
        options.gpio_slowdown = GPIO_SLOWDOWN
        options.disable_hardware_pulsing = not HAT_PWM_ENABLED
        options.drop_privileges = True
        self.matrix = RGBMatrix(options=options)

        # Setup canvas
        self.canvas = self.matrix.CreateFrameCanvas()
        self.canvas.Clear()

        # Data to render
        self._data_index = 0
        self._data = []
        self._data_all_looped = False

        # quiet hours state, re-checked once per second; seeded here so a
        # boot inside the off window doesn't flash frames 1-9 at full brightness
        startup_status = get_quiet_status()
        self._quiet_off = startup_status["mode"] == "off"
        self._applied_brightness = min(startup_status["brightness"], BRIGHTNESS)
        self.matrix.brightness = self._applied_brightness
        self.canvas.brightness = self._applied_brightness

        # Start Looking for planes
        self.overhead = Overhead()
        self.overhead.grab_data()

        # Initalise animator and scenes
        super().__init__()

        # Overwrite any default settings from
        # Animator or Scenes
        self.delay = frames.PERIOD

    def draw_square(self, x0, y0, x1, y1, colour):
        for x in range(x0, x1):
            _ = graphics.DrawLine(self.canvas, x, y0, x, y1, colour)

    @Animator.KeyFrame.add(0)
    def clear_screen(self):
        # First operation after
        # a screen reset
        self.canvas.Clear()

    @Animator.KeyFrame.add(frames.PER_SECOND * 5)
    def check_for_loaded_data(self, count):
        # skip flight data during quiet hours if configured
        if QUIET_HOURS_HIDE_FLIGHTS and should_display_be_dim():
            if self._data:
                self._data = []
                self.reset_scene()
            return

        if self.overhead.new_data:
            # Check if there's data
            there_is_data = len(self._data) > 0 or not self.overhead.data_is_empty

            # this marks self.overhead.data as no longer new
            new_data = self.overhead.data

            # See if this matches the data already on the screen
            # This test only checks if it's 2 lists with the same
            # callsigns, regardless or order
            data_is_different = not callsigns_match(self._data, new_data)

            if data_is_different:
                self._data_index = 0
                self._data_all_looped = False
                self._data = new_data

            # Only reset if there's flight data already
            # on the screen, of if there's some new
            # data available to draw which is different
            # from the current data
            reset_required = there_is_data and data_is_different

            if reset_required:
                self.reset_scene()

    @Animator.KeyFrame.add(frames.PER_SECOND)
    def check_quiet_hours(self, count):
        status = get_quiet_status()
        was_off = self._quiet_off
        self._quiet_off = status["mode"] == "off"

        # cap at configured BRIGHTNESS so normal mode restores it, not 100
        target = min(status["brightness"], BRIGHTNESS)
        if target != self._applied_brightness:
            # canvas too: with SwapOnVSync the offscreen canvas keeps its own brightness
            self.matrix.brightness = target
            self.canvas.brightness = target
            self._applied_brightness = target

        if was_off and not self._quiet_off:
            # scenes that only paint on change (e.g. clock) need a full redraw
            self.reset_scene()

    @Animator.KeyFrame.add(1)
    def zzzz_quiet_blank(self, count):
        # runs after all scene draws, before zzzzz_sync, so the off
        # window always swaps a black canvas
        if self._quiet_off:
            self.canvas.Clear()

    @Animator.KeyFrame.add(1)
    def zzzzz_sync(self, count):
        # zzzzz_ prefix ensures this runs LAST, after all drawing is complete
        _ = self.matrix.SwapOnVSync(self.canvas)

    @Animator.KeyFrame.add(frames.PER_SECOND * 30)
    def grab_new_data(self, count):
        # don't poll for flights during quiet hours if configured
        if QUIET_HOURS_HIDE_FLIGHTS and should_display_be_dim():
            return

        if not (self.overhead.processing and self.overhead.new_data) and (
            self._data_all_looped or len(self._data) <= 1
        ):
            self.overhead.grab_data()

    def run(self):
        try:
            # Start loop
            print("Press CTRL-C to stop")
            self.play()

        except KeyboardInterrupt:
            print("Exiting\n")
            sys.exit(0)
