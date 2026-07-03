from utilities.animator import Animator
from setup import colours, fonts, screen

from rgbmatrix import graphics

# window view cone for the direction indicator
try:
    from config import WINDOW_BEARING, WINDOW_FOV
except (ModuleNotFoundError, NameError, ImportError):
    WINDOW_BEARING = None
    WINDOW_FOV = None

# Setup
BAR_STARTING_POSITION = (0, 18)
BAR_PADDING = 2

FLIGHT_NO_POSITION = (1, 21)
FLIGHT_NO_TEXT_HEIGHT = 8  # based on font size
FLIGHT_NO_FONT = fonts.small

FLIGHT_NUMBER_ALPHA_COLOUR = colours.BLUE_LIGHT
FLIGHT_NUMBER_NUMERIC_COLOUR = colours.WHITE

DATA_INDEX_POSITION = (49, 21)
DATA_INDEX_TEXT_HEIGHT = 8
DATA_INDEX_FONT = fonts.small

DIVIDING_BAR_COLOUR = colours.GREEN
DATA_INDEX_COLOUR = colours.GREY

# window direction indicator: a tick on a short bar shows where in the
# window's field of view the flight sits; a chevron shows climb/descent.
# positions sit above the dividing bar, skipped if the callsign runs long
BEARING_BAR_X = 37
BEARING_BAR_Y = 15
BEARING_BAR_WIDTH = 7
BEARING_BAR_COLOUR = colours.BLUE_DARKER
BEARING_TICK_COLOUR = colours.WHITE
CHEVRON_X = 45
CHEVRON_Y = 14
CLIMB_COLOUR = colours.GREEN
DESCENT_COLOUR = colours.ORANGE
VERTICAL_SPEED_MEANINGFUL = 300  # fpm; below this treat as level flight


def window_offset(bearing):
    # -1 (left edge of view) to 1 (right edge), wraparound safe at 0/360
    diff = (bearing - WINDOW_BEARING + 180) % 360 - 180
    half_fov = WINDOW_FOV / 2
    return max(-1.0, min(1.0, diff / half_fov))


class FlightDetailsScene(object):
    def __init__(self):
        super().__init__()

    @Animator.KeyFrame.add(0)
    def flight_details(self):
        # skip while plane intro is playing
        if hasattr(self, 'is_intro_active') and self.is_intro_active():
            return

        # Guard against no data
        if len(self._data) == 0:
            return

        # Clear the whole area
        self.draw_square(
            0,
            BAR_STARTING_POSITION[1] - (FLIGHT_NO_TEXT_HEIGHT // 2),
            screen.WIDTH - 1,
            BAR_STARTING_POSITION[1] + (FLIGHT_NO_TEXT_HEIGHT // 2),
            colours.BLACK,
        )

        # Draw flight number if available
        flight_no_text_length = 0
        if (
            self._data[self._data_index]["callsign"]
            and self._data[self._data_index]["callsign"] != "N/A"
        ):
            flight_no = f'{self._data[self._data_index]["callsign"]}'

            for ch in flight_no:
                ch_length = graphics.DrawText(
                    self.canvas,
                    FLIGHT_NO_FONT,
                    FLIGHT_NO_POSITION[0] + flight_no_text_length,
                    FLIGHT_NO_POSITION[1],
                    FLIGHT_NUMBER_NUMERIC_COLOUR
                    if ch.isnumeric()
                    else FLIGHT_NUMBER_ALPHA_COLOUR,
                    ch,
                )
                flight_no_text_length += ch_length

        # Draw bar
        if len(self._data) > 1:
            # Clear are where N of M might have been
            self.draw_square(
                DATA_INDEX_POSITION[0] - BAR_PADDING,
                BAR_STARTING_POSITION[1] - (FLIGHT_NO_TEXT_HEIGHT // 2),
                screen.WIDTH,
                BAR_STARTING_POSITION[1] + (FLIGHT_NO_TEXT_HEIGHT // 2),
                colours.BLACK,
            )

            # Dividing bar
            graphics.DrawLine(
                self.canvas,
                flight_no_text_length + BAR_PADDING,
                BAR_STARTING_POSITION[1],
                DATA_INDEX_POSITION[0] - BAR_PADDING - 1,
                BAR_STARTING_POSITION[1],
                DIVIDING_BAR_COLOUR,
            )

            # Draw text
            text_length = graphics.DrawText(
                self.canvas,
                DATA_INDEX_FONT,
                DATA_INDEX_POSITION[0],
                DATA_INDEX_POSITION[1],
                DATA_INDEX_COLOUR,
                f"{self._data_index + 1}/{len(self._data)}",
            )
        else:
            # Dividing bar
            graphics.DrawLine(
                self.canvas,
                flight_no_text_length + BAR_PADDING if flight_no_text_length else 0,
                BAR_STARTING_POSITION[1],
                screen.WIDTH,
                BAR_STARTING_POSITION[1],
                DIVIDING_BAR_COLOUR,
            )

        self._draw_window_indicator(flight_no_text_length)

    def _draw_window_indicator(self, flight_no_text_length):
        flight = self._data[self._data_index]
        callsign_end = FLIGHT_NO_POSITION[0] + flight_no_text_length

        # bearing tick: left/center/right of the window's field of view
        bearing = flight.get("bearing")
        if (
            WINDOW_BEARING is not None
            and WINDOW_FOV
            and bearing is not None
            and callsign_end < BEARING_BAR_X
        ):
            graphics.DrawLine(
                self.canvas,
                BEARING_BAR_X,
                BEARING_BAR_Y,
                BEARING_BAR_X + BEARING_BAR_WIDTH - 1,
                BEARING_BAR_Y,
                BEARING_BAR_COLOUR,
            )

            offset = window_offset(bearing)
            if offset < -1 / 3:
                tick_x = BEARING_BAR_X
            elif offset > 1 / 3:
                tick_x = BEARING_BAR_X + BEARING_BAR_WIDTH - 1
            else:
                tick_x = BEARING_BAR_X + BEARING_BAR_WIDTH // 2

            for tick_y in range(BEARING_BAR_Y - 1, BEARING_BAR_Y + 2):
                self.canvas.SetPixel(
                    tick_x,
                    tick_y,
                    BEARING_TICK_COLOUR.red,
                    BEARING_TICK_COLOUR.green,
                    BEARING_TICK_COLOUR.blue,
                )

        # climb/descent chevron
        vertical_speed = flight.get("vertical_speed")
        if (
            vertical_speed is not None
            and abs(vertical_speed) > VERTICAL_SPEED_MEANINGFUL
            and callsign_end < CHEVRON_X
        ):
            if vertical_speed > 0:
                colour = CLIMB_COLOUR
                pixels = [(1, 0), (0, 1), (2, 1)]
            else:
                colour = DESCENT_COLOUR
                pixels = [(0, 0), (2, 0), (1, 1)]

            for dx, dy in pixels:
                self.canvas.SetPixel(
                    CHEVRON_X + dx,
                    CHEVRON_Y + dy,
                    colour.red,
                    colour.green,
                    colour.blue,
                )
