import logging

_LOGGER = logging.getLogger(__name__)

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

class MCP23017:
    def __init__(self, pi, i2c_bus, address):
        self.pi = pi
        self.address = address
        self.handle = pi.i2c_open(i2c_bus, address)

        # Configure MCP23017
        self._setup_mcp23017()

    def _setup_mcp23017(self):
        try:
            # Test if the device is present
            self.pi.i2c_read_byte_data(self.handle, IOCONA)

            config = 0 | CONF["HAEN"] | CONF["INTPOL"] | CONF["MIRROR"];
            # Configure the MCP23017
            self.pi.i2c_write_i2c_block_data(self.handle, IOCONB, [config, config])  # Update 

            # Set all ports as inputs with pull-ups
            self.pi.i2c_write_i2c_block_data(self.handle, IODIRA, 0xFFFF)  # All inputs
            self.pi.i2c_write_i2c_block_data(self.handle, GPPUA, 0xFFFF)   # Enable pull-ups
            self.pi.i2c_write_i2c_block_data(self.handle, IPOLA, 0x0000)

            # Enable interrupts on all pins (change from default)
            self.pi.i2c_write_i2c_block_data(self.handle, GPINTENA, 0xFFFF)  # Int enable
            self.pi.i2c_write_i2c_block_data(self.handle, INTCONA, 0x0000) #Int on change
            self.pi.i2c_write_i2c_block_data(self.handle, GPINTENA, 0xFFFF)
            self.pi.i2c_write_i2c_block_data(self.handle, DEFVALA, 0xFFFF)
            
            # Update configuration register
            self.pi.i2c_write_i2c_block_data(self.handle, GPIOA, 0xFFFF)

            # Clear interrupt flags
            self.read_captured_interrupt()

            _LOGGER.info(f"MCP23017 at address {hex(self.address)} initialized successfully")

        except Exception as e:
            _LOGGER.error(f"Failed to initialize MCP23017 at address {hex(self.address)}: {e}")
            raise

    def read_captured_interrupt(self) -> int:
        """Read interrupt capture register to clear interrupt flag"""
        (b, int_cap) = self.pi.i2c_read_i2c_block_data(self.handle, INTCAPA, 2)
        _LOGGER.debug(f"Captured interrupt: {int_cap[0]:08b}-{int_cap[1]:08b}")

        return int_cap[0] | (int_cap[1] << 8)

    def get_interrupt_flag(self) -> int:
        """Get current interrupt status for both ports"""
        (b, intf) = self.pi.i2c_read_i2c_block_data(self.handle, INTFA, 2)
        _LOGGER.debug(f"Interrupt status: {intf[0]:08b}-{intf[1]:08b}")
        
        return intf[0] | (intf[1] << 8)

    def read_gpio(self) -> int:
        """Read current GPIO state"""
        (b, data) = self.pi.i2c_read_i2c_block_data(self.handle, GPIOA, 2)
        _LOGGER.debug(f"GPIO Values: {data[0]:08b}-{data[1]:08b}")

        return data[0] | (data[1] << 8)

    def cleanup(self):
        self.pi.i2c_close(self.handle)
