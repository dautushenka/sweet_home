from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.const import CONF_DEVICE_CLASS
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from .connected_device import ConnectedPinInterface
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from .io_pi_plus import IO_Pi_Plus

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_ADDRESS,
    CONF_PIN,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    # This is for config entry setup - sensors are created dynamically 
    # through YAML configuration or other means
    pass


def setup_platform(
    hass: HomeAssistant,
    config: dict,
    add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up the platform (legacy YAML support)."""
    try:
        address = config[CONF_ADDRESS]
        pin = config[CONF_PIN]
        sensor = SweetHomeBinarySensor(int(address, 16), int(pin));

        add_entities([sensor], True)
        IO_Pi_Plus.addConnectedPins([sensor])
        
    except (ValueError, KeyError) as err:
        _LOGGER.error("Error setting up binary sensor: %s", err)


class SweetHomeBinarySensor(BinarySensorEntity, ConnectedPinInterface):
    """Representation of a Sweet Home binary sensor."""
    
    def __init__(self, address: int, pin: int) -> None:
        """Initialize the binary sensor."""
        super().__init__()
        self.address = address
        self.pin = pin
        self._attr_should_poll = False
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"{DOMAIN}-{hex(address)}-{pin}"
        self._attr_name = f"Binary sensor {hex(address)}-{pin}"

    def getAddress(self) -> int:
        return self.address
    
    def getPinNumber(self) -> int:
        return self.pin

    def onChange(self, value: int) -> None:
        """Handle value change from MCP23017."""
        self._attr_is_on = value > 0
        self.schedule_update_ha_state()
        
    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        # Remove from MCP23017 handler if needed
        pass