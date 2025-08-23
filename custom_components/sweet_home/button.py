import time
import threading as th
from homeassistant.core import HomeAssistant
from homeassistant.util.async_ import run_callback_threadsafe

from homeassistant.const import CONF_DEVICE_ID, CONF_TYPE
from .connected_device import ConnectedPinInterface
from .const import (
    EVENT_TYPE,
    CONF_SUBTYPE,
    EVENT_DOUBLE_PRESS,
    EVENT_SINGLE_PRESS,
    EVENT_LONG_PRESS,
    EVENT_TRIPLE_PRESS,
)

NEXT_PRESS_THRESHOLD = 300  # milliseconds
LONG_PRESS_THRESHOLD = 1000  # milliseconds


class Button(ConnectedPinInterface):
    hass: HomeAssistant = None
    device_id: str
    subtype: str

    address: int = None
    pin: int = None
    presses: int = 1
    pressed_time: float = 0
    pressed_count: int = 0

    longPressTimer: th.Timer = None
    nextPressTimer: th.Timer = None

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        subtype: str,
        address: int,
        pin: int,
        presses: int,
    ) -> None:
        self.hass = hass
        self.device_id = device_id
        self.subtype = subtype

        self.address = address
        self.pin = pin
        self.presses = presses

    def getAddress(self) -> int:
        return self.address
    
    def getPinNumber(self) -> int:
        return self.pin

    def __reset(self) -> None:
        self.pressed_time = 0
        self.pressed_count = 0
        self.__resetLongPressTimer()
        self.__resetNextPressTimer()

    def __resetLongPressTimer(self) -> None:
        if self.longPressTimer is not None:
            self.longPressTimer.cancel()
            self.longPressTimer = None

    def __resetNextPressTimer(self) -> None:
        if self.nextPressTimer is not None:
            self.nextPressTimer.cancel()
            self.nextPressTimer = None

    def __executeLongPress(self) -> None:
        self.__fireHassEvent(EVENT_LONG_PRESS)
        # print("fire long press {}".format(self.pressed_count))
        self.__reset()

    def __execPresses(self) -> None:
        event_type = EVENT_SINGLE_PRESS
        if (self.pressed_count == 2):
            event_type = EVENT_DOUBLE_PRESS
        elif (self.pressed_count == 3):
            event_type = EVENT_TRIPLE_PRESS

        self.__fireHassEvent(event_type)
        self.__reset()

    def __fireHassEvent(self, type: str):
        # Fire event
        data = {
            CONF_DEVICE_ID: self.device_id,
            CONF_TYPE: type,
            CONF_SUBTYPE: self.subtype,
        }
        # Use async_add_job to ensure the event is fired within the event loop
        run_callback_threadsafe(
            self.hass.loop,
            self.hass.bus.async_fire,
            EVENT_TYPE,
            data
        )
        # self.hass.async_add_job(self.hass.bus.async_fire, EVENT_TYPE, data)

    def onChange(self, value: int) -> None:
        if value == 0:
            self.pressed_time = time.time()
            self.pressed_count += 1
            self.__resetNextPressTimer()
            self.longPressTimer = th.Timer(
                LONG_PRESS_THRESHOLD / 1000, self.__executeLongPress
            )
            self.longPressTimer.start()
        elif self.pressed_time > 0:
            duration = (time.time() - self.pressed_time) * 1000  # Convert to milliseconds
            self.pressed_time = 0
            self.__resetLongPressTimer()
            if duration < LONG_PRESS_THRESHOLD:
                if self.presses == self.pressed_count:
                    self.__execPresses()
                else:
                    self.nextPressTimer = th.Timer(
                        NEXT_PRESS_THRESHOLD / 1000, self.__execPresses
                    )
                    self.nextPressTimer.start()
                    
    def cleanup(self) -> None:
        """Clean up timers on integration unload."""
        self.__resetLongPressTimer()
        self.__resetNextPressTimer()
