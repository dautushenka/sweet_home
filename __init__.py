from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr

from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_NAME,
)

from .const import (
    CONF_ADDRESS,
    DOMAIN,
    CONF_BUTTONS,
    CONF_PIN,
    CONF_NAME,
    CONF_SWITCHES,
    CONF_ID,
    CONF_PRESS_COUNT,
    DATA_KEY_CONFIG,
    DATA_KEY_BUTTONS,
    EVENT_DOUBLE_PRESS,
    EVENT_TRIPLE_PRESS,
    EVENT_SINGLE_PRESS,
)

from .button import Button

from .mcp23017 import Run, setButtons
import RPi.GPIO as GPIO

_LOGGER = logging.getLogger(__name__)

BUTTON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Required(CONF_PIN): cv.string,
        vol.Optional(CONF_PRESS_COUNT, default=EVENT_SINGLE_PRESS): vol.In(
            [EVENT_DOUBLE_PRESS, EVENT_TRIPLE_PRESS, EVENT_SINGLE_PRESS]
        ),
    }
)

SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ID): cv.string,
        vol.Required(CONF_BUTTONS): vol.All(cv.ensure_list, [BUTTON_SCHEMA]),
    }
)

# Schema to validate the configured MQTT topic
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_SWITCHES): vol.All(cv.ensure_list, [SWITCH_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data[DOMAIN] = {}
    if DOMAIN in config:
        hass.data[DOMAIN][DATA_KEY_CONFIG] = config[DOMAIN]

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Start setuping entry")
    config = hass.data[DOMAIN][DATA_KEY_CONFIG]
    # hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    if CONF_SWITCHES not in config:
        _LOGGER.info("There are not switches in config")
        return True

    switches = config[CONF_SWITCHES]

    device_registry = dr.async_get(hass)
    buttons: dict[str, list[Button]] = {}
    for swt in switches:
        params = {
            ATTR_IDENTIFIERS: {(DOMAIN, swt["id"])},
            ATTR_MANUFACTURER: "Raspberry Pi mcp23017",
            ATTR_NAME: swt["name"],
        }
        device_entry = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id, **params
        )
        buttons[device_entry.id] = []
        for idx, btn in enumerate(swt[CONF_BUTTONS]):
            presses = 1
            if btn.get(CONF_PRESS_COUNT) is not None:
                if btn[CONF_PRESS_COUNT] == EVENT_DOUBLE_PRESS:
                    presses = 2
                elif btn[CONF_PRESS_COUNT] == EVENT_TRIPLE_PRESS:
                    presses = 3
            buttons[device_entry.id].append(
                Button(
                    hass=hass,
                    device_id=device_entry.id,
                    subtype="button_" + str(idx + 1),
                    address=int(btn[CONF_ADDRESS], 16),
                    pin=int(btn[CONF_PIN]),
                    presses=presses,
                )
            )

    hass.data[DOMAIN][DATA_KEY_BUTTONS] = buttons
    _LOGGER.info("Run handling buttons on mcp23017")
    setButtons(buttons)
    Run(_LOGGER)

    # hass.async_add_job(hass.config_entries.flow.async_init(
    #     DOMAIN
    # ))

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True
