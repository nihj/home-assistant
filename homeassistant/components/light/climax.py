"""
Support for Climax lights.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.climax/
"""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ENTITY_ID_FORMAT,
    SUPPORT_BRIGHTNESS, Light)
from homeassistant.components.climax import (
    CLIMAX_CONTROLLER, CLIMAX_DEVICES, ClimaxDevice)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['climax']


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Climax lights."""
    add_entities(
        [ClimaxLight(device, hass.data[CLIMAX_CONTROLLER]) for
         device in hass.data[CLIMAX_DEVICES]['light']], True)


class ClimaxLight(ClimaxDevice, Light):
    """Representation of a Climax Light, including dimmable."""

    def __init__(self, climax_device, controller):
        """Initialize the light."""
        self._state = False
        self._brightness = None
        ClimaxDevice.__init__(self, climax_device, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.climax_id)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    def turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs and self.climax_device.is_dimmable:
            self.climax_device.set_brightness(kwargs[ATTR_BRIGHTNESS])
        else:
            self.climax_device.switch_on()

        self._state = True
        self.schedule_update_ha_state(True)

    def turn_off(self, **kwargs):
        """Turn the light off."""
        self.climax_device.switch_off()
        self._state = False
        self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def update(self):
        """Call to update state."""
        self._state = self.climax_device.is_switched_on()
        if self.climax_device.is_dimmable:
            # If it is dimmable, both functions exist. In case color
            # is not supported, it will return None
            self._brightness = self.climax_device.get_brightness()
