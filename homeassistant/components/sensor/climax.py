"""
Support for Climax sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.climax/
"""
import logging
from datetime import timedelta

from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT)
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.util import convert
from homeassistant.components.climax import (
    CLIMAX_CONTROLLER, CLIMAX_DEVICES, ClimaxDevice)

DEPENDENCIES = ['climax']

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Climax controller devices."""
    add_entities(
        [ClimaxSensor(device, hass.data[CLIMAX_CONTROLLER])
         for device in hass.data[CLIMAX_DEVICES]['sensor']], True)


class ClimaxSensor(ClimaxDevice, Entity):
    """Representation of a Climax Sensor."""

    def __init__(self, climax_device, controller):
        """Initialize the sensor."""
        self.current_value = None
        self._temperature_units = None
        self.last_changed_time = None
        ClimaxDevice.__init__(self, climax_device, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.climax_id)

    @property
    def state(self):
        """Return the name of the sensor."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        import pyclimax as climaxApi
        if self.climax_device.type == climaxApi.CATEGORY_TEMPERATURE_SENSOR:
            return self._temperature_units
        if self.climax_device.type == climaxApi.CATEGORY_POWER_METER:
            return 'watts'

    def update(self):
        """Update the state."""
        import pyclimax as climaxApi
        if self.climax_device.type == climaxApi.CATEGORY_TEMPERATURE_SENSOR:
            self.current_value = self.climax_device.temperature

            climax_temp_units = (
                self.climax_device.climax_controller.temperature_units)

            if climax_temp_units == 'F':
                self._temperature_units = TEMP_FAHRENHEIT
            else:
                self._temperature_units = TEMP_CELSIUS

        elif self.climax_device.type == climaxApi.CATEGORY_POWER_METER:
            energy = convert(self.climax_device.energy, float, 0)
            self.current_value = int(round(energy, 0))
        else:
            self.current_value = 'Unknown'
