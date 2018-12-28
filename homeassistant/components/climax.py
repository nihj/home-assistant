"""
Support for Climax devices.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/climax/
"""
import logging
from collections import defaultdict

import voluptuous as vol
from requests.exceptions import RequestException

from homeassistant.util.dt import utc_from_timestamp
from homeassistant.util import convert, slugify
from homeassistant.helpers import discovery
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP, CONF_LIGHTS, CONF_EXCLUDE)
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['pyclimax==0.0.1']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'climax'

CLIMAX_CONTROLLER = 'climax_controller'

CONF_CONTROLLER_URL = 'climax_controller_url'
CONF_CONTROLLER_USERNAME = 'climax_controller_username'
CONF_CONTROLLER_PASSWORD = 'climax_controller_password'

CLIMAX_ID_FORMAT = '{}_{}'

ATTR_CURRENT_POWER_W = "current_power_w"
ATTR_CURRENT_ENERGY_KWH = "current_energy_kwh"

CLIMAX_DEVICES = 'climax_devices'

CLIMAX_ID_LIST_SCHEMA = vol.Schema([str])

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_CONTROLLER_URL): cv.url,
        vol.Required(CONF_CONTROLLER_USERNAME): cv.string,
        vol.Required(CONF_CONTROLLER_PASSWORD): cv.string,
        vol.Optional(CONF_EXCLUDE, default=[]): CLIMAX_ID_LIST_SCHEMA,
        vol.Optional(CONF_LIGHTS, default=[]): CLIMAX_ID_LIST_SCHEMA
    }),
}, extra=vol.ALLOW_EXTRA)

CLIMAX_COMPONENTS = [
    'sensor', 'light', 'switch'
]


def setup(hass, base_config):
    """Set up for Climax devices."""
    import pyclimax as climaxApi

    def stop_subscription(event):
        """Shutdown Climax subscriptions and subscription thread on exit."""
        _LOGGER.info("Shutting down subscriptions")
        hass.data[CLIMAX_CONTROLLER].stop()

    config = base_config.get(DOMAIN)

    # Get Climax specific configuration.
    base_url = config.get(CONF_CONTROLLER_URL)
    username = config.get(CONF_CONTROLLER_USERNAME)
    password = config.get(CONF_CONTROLLER_PASSWORD)
    light_ids = config.get(CONF_LIGHTS)
    exclude_ids = config.get(CONF_EXCLUDE)

    # Initialize the Climax controller.
    controller, _ = climaxApi.init_controller(base_url, username, password)
    hass.data[CLIMAX_CONTROLLER] = controller
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_subscription)

    try:
        print('NIKLAS: Getting all devices')
        all_devices = controller.get_devices()

    except RequestException:
        # There was a network related error connecting to the Climax controller.
        _LOGGER.exception("Error communicating with Climax API")
        return False

    # Exclude devices unwanted by user.
    devices = [device for device in all_devices
               if device.device_id not in exclude_ids]

    climax_devices = defaultdict(list)
    for device in devices:
        print('NIKLAS: Adding device')
        device_type = map_climax_device(device, light_ids)
        if device_type is None:
            print('NIKLAS Device type is None')
            continue

        climax_devices[device_type].append(device)
    hass.data[CLIMAX_DEVICES] = climax_devices

    for component in CLIMAX_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, base_config)

    return True


def map_climax_device(climax_device, remap):
    """Map climax classes to Home Assistant types."""
    import pyclimax as climaxApi
    if isinstance(climax_device, climaxApi.ClimaxDimmer):
        return 'light'
    if isinstance(climax_device, climaxApi.ClimaxSensor):
        return 'sensor'
    if isinstance(climax_device, climaxApi.ClimaxSwitch):
        if climax_device.device_id in remap:
            return 'light'
        return 'switch'
    return None


class ClimaxDevice(Entity):
    """Representation of a Climax device entity."""

    def __init__(self, climax_device, controller):
        """Initialize the device."""
        self.climax_device = climax_device
        self.controller = controller

        self._name = self.climax_device.name
        # Append device id to prevent name clashes in HA.
        self.climax_id = CLIMAX_ID_FORMAT.format(
            slugify(climax_device.name), climax_device.device_id)

        self.controller.register(climax_device, self._update_callback)

    def _update_callback(self, _device):
        """Update the state."""
        self.schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        """Get polling requirement from climax device."""
        return self.climax_device.should_poll

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        import pyclimax as climaxApi
        attr = {}

        if isinstance(self.climax_device, climaxApi.ClimaxSwitch):
            power = self.climax_device.power
            if power:
                attr[ATTR_CURRENT_POWER_W] = convert(power, float, 0.0)

        if isinstance(self.climax_device, climaxApi.ClimaxSensor):
            energy = self.climax_device.energy
            if energy:
                attr[ATTR_CURRENT_ENERGY_KWH] = convert(energy, float, 0.0)

        attr['Climax Device Id'] = self.climax_device.climax_device_id

        return attr

    @property
    def unique_id(self) -> str:
        """Return a unique ID.

        The Climax assigns a unique and immutable ID number to each device.
        """
        return str(self.climax_device.climax_device_id)
