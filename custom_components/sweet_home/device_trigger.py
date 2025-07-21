import logging
from homeassistant.const import (
    CONF_TYPE,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
)
from .const import (
    DOMAIN,
    CONF_PRESS_COUNT,
    CONF_BUTTONS,
    CONF_SWITCHES,
    EVENT_SINGLE_PRESS,
    EVENT_DOUBLE_PRESS,
    EVENT_TRIPLE_PRESS,
    EVENT_LONG_PRESS,
    DATA_KEY_CONFIG,
    DATA_KEY_BUTTONS,
    CONF_SUBTYPE,
    EVENT_TYPE,
)
from .button import Button

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
import voluptuous as vol

from homeassistant.core import CALLBACK_TYPE, callback, HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo

_LOGGER = logging.getLogger(__name__)

TRIGGER_TYPES = {EVENT_SINGLE_PRESS, EVENT_DOUBLE_PRESS, EVENT_TRIPLE_PRESS, EVENT_LONG_PRESS}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): str,
        vol.Required(CONF_SUBTYPE): str,
    }
)


async def async_get_triggers(hass, device_id):
    _LOGGER.debug("async_get_triggers2")
    """Return a list of triggers."""
    if DOMAIN not in hass.data:
        return []

    dev_reg: dr.DeviceRegistry = dr.async_get(hass)
    if (device_entry := dev_reg.async_get(device_id)) is None:
        raise ValueError(f"Device ID {device_id} is not valid")

    switch_id = get_device_id(device_entry)
    if switch_id is None:
        return []

    triggers = []
    buttons: dict[str, list[Button]] = hass.data[DOMAIN][DATA_KEY_BUTTONS]

    if device_id not in buttons:
        return triggers
    
    _LOGGER.debug("Start populate triggers")
    for btn in buttons[device_id]:
        trigger_base = {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_entry.id,
            CONF_SUBTYPE: btn.subtype
        }
        triggers.append({
            **trigger_base,
            CONF_TYPE: EVENT_SINGLE_PRESS,
        })
        triggers.append({
            **trigger_base,
            CONF_TYPE: EVENT_LONG_PRESS,
        })

        if btn.presses > 1:
            triggers.append({
                **trigger_base,
                CONF_TYPE: EVENT_DOUBLE_PRESS,
            })

            if btn.presses > 2:
                triggers.append({
                    **trigger_base,
                    CONF_TYPE: EVENT_TRIPLE_PRESS,
                })
    _LOGGER.debug(f"switch {switch_id} count tiggers {len(triggers)}")
    return triggers

async def async_attach_trigger(
        hass: HomeAssistant,
        config: ConfigType,
        action: TriggerActionType,
        trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Listen for state changes based on configuration."""
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_TYPE,
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_TYPE: config[CONF_TYPE],
                CONF_SUBTYPE: config[CONF_SUBTYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )


@callback
def get_device_id(device_entry: DeviceEntry) -> str | None:
    return next(
        (
            identifier[1]
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        ),
        None,
    )
