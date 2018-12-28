"""
Support for Climax switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.climax/
"""
import logging

from homeassistant.util import convert
from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchDevice
from homeassistant.components.climax import (
    CLIMAX_CONTROLLER, CLIMAX_DEVICES, ClimaxDevice)

DEPENDENCIES = ['climax']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Climax switches."""
    add_entities(
        [ClimaxSwitch(device, hass.data[CLIMAX_CONTROLLER]) for
         device in hass.data[CLIMAX_DEVICES]['switch']], True)


class ClimaxSwitch(ClimaxDevice, SwitchDevice):
    """Representation of a Climax Switch."""

    def __init__(self, climax_device, controller):
        """Initialize the Climax device."""
        self._state = False
        ClimaxDevice.__init__(self, climax_device, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.climax_id)

    def turn_on(self, **kwargs):
        """Turn device on."""
        self.climax_device.switch_on()
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn device off."""
        self.climax_device.switch_off()
        self._state = False
        self.schedule_update_ha_state()

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        power = self.climax_device.power
        if power:
            return convert(power, float, 0.0)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def update(self):
        """Update device state."""
        self._state = self.climax_device.is_switched_on()
