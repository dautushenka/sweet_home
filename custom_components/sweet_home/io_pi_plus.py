

import logging
import math
import time
import pigpio

from .connected_pin import ConnectedPinInterface
from .mcp23017 import MCP23017


_LOGGER = logging.getLogger(__name__)

INTERRUPTION_PIN_NUMBER = 27

class _IO_Pi_Plus:
    # {device_address -> {pin -> Button}}
    connected_pins: dict[int, dict[int, ConnectedPinInterface]]
    mcps: list[MCP23017]

    def __init__(self):
        self.connected_pins = {}
        self.pi = pigpio.pi()

    def addConnectedPins(self, pins: list[ConnectedPinInterface]):
        for pin in pins:
            if pin.getPinNumber() not in self.connected_pins[pin.getAddress()]:
                self.connected_pins[pin.getAddress()] = {}
            self.connected_pins[pin.getAddress()][pin.getPinNumber()] = pin
        
    def run(self):
        if not self.pi.connected:
            _LOGGER.error("Failed to connect to pigpio daemon. Is it running?")
            return

        try:
            self.mcps = [MCP23017(self.pi, 1, 0x20), MCP23017(self.pi, 1, 0x21)];

            def interruption_callback(gpio, level, tick):
                try:
                    _LOGGER.debug(f"Rising edge detected on GPIO{gpio} at tick {tick}, level {level}")
                    time.sleep(10/1000)
                    for mcp in self.mcps:
                        flag = mcp.get_interrupt_flag()
                        if flag == 0:
                            continue

                        # Check if the interrupted pin is in the buttons list
                        value = mcp.read_captured_interrupt() & flag;
                        interrupted_pin = math.log(flag, 2)

                        _LOGGER.debug(f"Interrupt flag: {flag:08b} (pin: {interrupted_pin}) on MCP {hex(mcp.address)}")
                    
                        if not interrupted_pin in self.connected_pins[mcp.address]:
                            _LOGGER.debug(f"Pin {interrupted_pin} not found in connected pins list")
                            break
                        
                        pin = self.connected_pins[mcp.address][interrupted_pin]
                        _LOGGER.debug(f"Send change event to pin {interrupted_pin}, value {1 if value > 0 else 0}")
                        pin.onChange(1 if value > 0 else 0)
                except Exception as e:
                    _LOGGER.error(f"Failed to handle interruption: {e}")
                    return
            
            _LOGGER.debug(f"Set up interruption callback on pin {INTERRUPTION_PIN_NUMBER}")
            self.pi.set_mode(INTERRUPTION_PIN_NUMBER, pigpio.INPUT)
            self.pi.set_pull_up_down(INTERRUPTION_PIN_NUMBER, pigpio.PUD_OFF)
            self.pi.set_glitch_filter(INTERRUPTION_PIN_NUMBER, 5000)
            self.cb = self.pi.callback(INTERRUPTION_PIN_NUMBER, pigpio.RISING_EDGE, interruption_callback)

        except Exception as e:
            _LOGGER.error(f"Failed to set up interruption callback: {e}")
            return

    def cleanup(self):
        self.connected_pins = {}
        self.mcps = []
        self.pi.stop();
        for mcp in self.mcps:
            mcp.cleanup()

        if self.cb is not None:
            self.cb.cancel()

    def __del__(self):
        self.cleanup()




IO_Pi_Plus = _IO_Pi_Plus()