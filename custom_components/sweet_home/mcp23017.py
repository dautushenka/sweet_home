import smbus
import signal
import time
# import pigpio
import RPi.GPIO as GPIO
from .button import Button
from .binary_sensor import SweetHomeBinarySensor


# Define registers values from datasheet
IODIRA = 0x00  # IO direction A - 1= input 0 = output
IODIRB = 0x01  # IO direction B - 1= input 0 = output
IPOLA = 0x02  # Input polarity A
IPOLB = 0x03  # Input polarity B
GPINTENA = 0x04  # Interrupt-onchange A
GPINTENB = 0x05  # Interrupt-onchange B
DEFVALA = 0x06  # Default value for port A
DEFVALB = 0x07  # Default value for port B
INTCONA = 0x08  # Interrupt control register for port A
INTCONB = 0x09  # Interrupt control register for port B
IOCONA = 0x0A  # Configuration register
IOCONB = 0x0B  # Configuration register
GPPUA = 0x0C  # Pull-up resistors for port A
GPPUB = 0x0D  # Pull-up resistors for port B
INTFA = 0x0E  # Interrupt condition for port A
INTFB = 0x0F  # Interrupt condition for port B
INTCAPA = 0x10  # Interrupt capture for port A
INTCAPB = 0x11  # Interrupt capture for port B
GPIOA = 0x12  # Data port A
GPIOB = 0x13  # Data port B
OLATA = 0x14  # Output latches A
OLATB = 0x15  # Output latches B

CONF = {
    "INTPOL": 1 << 1,  # This bit sets the polarity of the INT output pin
    "ODR": 1 << 2,  # Configures the INT pin as an open-drain output
    "HAEN": 1 << 3,  # Hardware Address Enable bit
    "SEQOP": 1 << 5,  # Sequential Operation mode bit
    "MIRROR": 1 << 6,  # INT Pins Mirror bit
    "BANK": 1 << 7,  # Controls how the registers are addressed
}

MCP23017_0X20 = 0x20
MCP23017_0X21 = 0x21


i2caddresses = {MCP23017_0X20, MCP23017_0X21}
code2buttons: dict[str, Button] = {}
code2sensors: dict[str, SweetHomeBinarySensor] = {}

def get_button_code(address, port, pin):
    return "{}-{}-{}".format(hex(address), hex(port), pin)

def setButtons(buttons: dict[str, list[Button]]):
    for btns in buttons.values():
        for b in btns:
            port = GPIOB if b.pin > 7 else GPIOA
            pin = b.pin if b.pin < 8 else b.pin - 8
            code2buttons[get_button_code(b.address, port, pin)] = b

def addBynarySensor(sensor: SweetHomeBinarySensor):
    port = GPIOB if sensor.pin > 7 else GPIOA
    pin = sensor.pin if sensor.pin < 8 else sensor.pin - 8
    code2sensors[get_button_code(sensor.address, port, pin)] = sensor

def initialize_mcp23017(logger):
    i2cbus = smbus.SMBus(1)
    logger.info("Configure mcp23017")
    for i2caddress in i2caddresses:
        i2cbus.write_byte_data(
            i2caddress, IOCONA, 0 | CONF["HAEN"] | CONF["INTPOL"] | CONF["MIRROR"]
        )  # Update configuration register
        i2cbus.write_byte_data(
            i2caddress, IOCONB, 0 | CONF["HAEN"] | CONF["INTPOL"] | CONF["MIRROR"]
        )  # Update configuration register
        i2cbus.write_byte_data(i2caddress, IPOLA, 0x00)
        i2cbus.write_byte_data(i2caddress, IPOLB, 0x00)
        i2cbus.write_byte_data(i2caddress, IODIRA, 0xFF)
        i2cbus.write_byte_data(i2caddress, IODIRB, 0xFF)
        i2cbus.write_byte_data(i2caddress, GPINTENA, 0xFF)
        i2cbus.write_byte_data(i2caddress, GPINTENB, 0xFF)
        i2cbus.write_byte_data(i2caddress, INTCONA, 0x00)
        i2cbus.write_byte_data(i2caddress, INTCONB, 0x00)
        i2cbus.write_byte_data(i2caddress, GPPUA, 0xFF)
        i2cbus.write_byte_data(i2caddress, GPPUB, 0xFF)
        i2cbus.write_byte_data(i2caddress, DEFVALA, 0xFF)
        i2cbus.write_byte_data(i2caddress, DEFVALB, 0xFF)
        i2cbus.write_byte_data(i2caddress, GPIOA, 0xFF)
        i2cbus.write_byte_data(i2caddress, GPIOB, 0xFF)

        i2cbus.read_byte_data(i2caddress, INTCAPA)
        i2cbus.read_byte_data(i2caddress, INTCAPB)
        i2cbus.read_byte_data(i2caddress, INTFA)
        i2cbus.read_byte_data(i2caddress, INTFB)

    i2cbus.close()
    logger.info("MCP23017 initialized")

def Run(logger):
    # pi = pigpio.pi()
    # if not pi.connected:
        # logger.error("Could not connect to pigpiod")
        # return

    initialize_mcp23017(logger)

    def get_data_code(address, port):
        return "{}-{}".format(address, port)

    prev_datas = {}

    def get_interruption_callback(address):
        def interruption_callback(channel):
            logger.debug("Interrupt is occurred on device {}".format(hex(address)))
            time.sleep(20 / 1000)
            try:
                i2cbus = smbus.SMBus(1)
                for port in [GPIOA, GPIOB]:
                    data = i2cbus.read_byte_data(address, port)
                    data_code = get_data_code(address, port)
                    prev_data = prev_datas.get(data_code, 0xFF)
                    prev_datas[data_code] = data
                    logger.debug("port {} data {}".format(hex(port), bin(data)))
                    for x in range(8):
                        value = data & (1 << x)
                        button_code = get_button_code(address, port, x)
                        if prev_data & (1 << x) != value:
                            logger.debug(
                                "Changed pin {} to {}".format(button_code, value)
                            )
                            button = code2buttons.get(button_code)
                            sensor = code2sensors.get(button_code)
                            if button is not None:
                                logger.debug(
                                    "Send change event to button {}".format(button_code)
                                )
                                button.onChange(value)
                            elif sensor is not None:
                                logger.debug(
                                    "Send change event to bynary sensor {}".format(button_code)
                                )
                                sensor.onChange(value)
                i2cbus.close()
            except Exception as e:
                logger.error("Error in interruption callback: {}".format(e))

        return interruption_callback

    INTERRUPT_PIN_X20 = 27  # pin 13 / 7
    INTERRUPT_PIN_X21 = 22  # pin 15 / 8

    logger.info(
        "Configure GPIO and attach interruptions on ports {}, {}".format(
            INTERRUPT_PIN_X20, INTERRUPT_PIN_X21
        )
    )
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(INTERRUPT_PIN_X20, GPIO.IN)
    GPIO.setup(INTERRUPT_PIN_X21, GPIO.IN)

    GPIO.add_event_detect(
        INTERRUPT_PIN_X20,
        GPIO.RISING,
        callback=get_interruption_callback(MCP23017_0X20),
    )
    GPIO.add_event_detect(
        INTERRUPT_PIN_X21,
        GPIO.RISING,
        callback=get_interruption_callback(MCP23017_0X21),
    )

    def signal_handler(sig, frame):
        i2cbus.close()
        GPIO.cleanup()

    signal.signal(signal.SIGINT, signal_handler)
