"""
Support for Control4 Thermostat. You need to use control4-2way-web-driver
along with this
"""
import asyncio
import logging

import aiohttp
import async_timeout
import voluptuous as vol
import urllib.parse as urlparse
from urllib.parse import urlencode
import json

from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
<<<<<<< HEAD
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_TIMEOUT,
    TEMP_FAHRENHEIT,
    TEMP_CELSIUS, 
    ATTR_TEMPERATURE,
)
=======
    STATE_HEAT, STATE_COOL, STATE_IDLE, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, ATTR_CURRENT_TEMPERATURE,
    ATTR_OPERATION_MODE, STATE_AUTO, SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE_HIGH, SUPPORT_TARGET_TEMPERATURE_LOW, SUPPORT_OPERATION_MODE, )
from homeassistant.const import (CONF_NAME, CONF_TIMEOUT, TEMP_FAHRENHEIT,
        TEMP_CELSIUS, STATE_OFF, STATE_ON, ATTR_TEMPERATURE)
>>>>>>> parent of 14c0cca... initial changes - not done
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template
from homeassistant.util.async_ import run_callback_threadsafe
from homeassistant.util.async_ import run_coroutine_threadsafe

CONF_BASE_URL = 'base_url'
CONF_PROXY_ID = 'proxy_id'

DEFAULT_NAME = 'Control4 Light'
DEFAULT_TIMEOUT = 10
<<<<<<< HEAD
STATE_VARIABLE_ID = '1107'
<<<<<<< HEAD
MODE_VARIABLE_ID = '1104'
=======
STATE_VARIABLE_ID = '1104'
OPERATION_VARIABLE_ID = '1104'
>>>>>>> parent of 14c0cca... initial changes - not done
=======
OPERATION_VARIABLE_ID = '1104'
>>>>>>> parent of 19db603... more changes - seems that it should work now
CURRENT_TEMP_VARIABLE_ID = '1131'
UNIT_VARIABLE_ID = '1100'
TARGET_TEMP_HIGH_VARIABLE_ID = '1135'
TARGET_TEMP_LOW_VARIABLE_ID = '1133'

<<<<<<< HEAD
<<<<<<< HEAD
=======
#SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_HIGH | SUPPORT_TARGET_TEMPERATURE_LOW | SUPPORT_OPERATION_MODE)
>>>>>>> parent of 19db603... more changes - seems that it should work now
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE)

STATE_MAPPING = {
    "Off": HVAC_MODE_OFF,
    "Cool": HVAC_MODE_COOL,
    "Heat": HVAC_MODE_HEAT,
    "Auto": HVAC_MODE_HEAT_COOL
=======
#SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_HIGH | SUPPORT_TARGET_TEMPERATURE_LOW | SUPPORT_OPERATION_MODE)
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE)

STATE_MAPPING = {
    "Off": STATE_OFF,
    "Cool": STATE_COOL,
    "Heat": STATE_HEAT,
    "Auto": STATE_AUTO
>>>>>>> parent of 14c0cca... initial changes - not done
}

OPERATION_MAPPING = {
    "Off": STATE_IDLE,
    "Cool": STATE_COOL,
    "Heat": STATE_HEAT
}

UNIT_MAPPING = {
    "FAHRENHEIT": TEMP_FAHRENHEIT,
    "CELSIUS": TEMP_CELSIUS
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_BASE_URL): cv.url,
    vol.Required(CONF_PROXY_ID): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument,
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    base_url = config.get(CONF_BASE_URL)
    proxy_id = config.get(CONF_PROXY_ID)
    timeout = config.get(CONF_TIMEOUT)

    yield from async_add_devices(
        [C4ClimateDevice(hass, name, base_url, proxy_id, timeout)])

class C4ClimateDevice(ClimateDevice):

    def __init__(self, hass, name, base_url, proxy_id, timeout):
        self._state = STATE_OFF
        self._operation = STATE_IDLE
        self.hass = hass
        self._name = name
        self._base_url = base_url;
        self._proxy_id = proxy_id;
        self._timeout = timeout
        self._current_temp = 0
       # self._target_temp_high = 0
        self._target_temp = 0
        self._unit = TEMP_FAHRENHEIT
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_AUTO]

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._operation_list

    @property
    def temperature_unit(self):
        return self._unit

    @property
    def precision(self):
        return 1

    @property
    def current_temperature(self):
        return self._current_temp

    @property
    def current_operation(self):
        return self._operation

    @property
    def target_temperature_high(self):
        return self._target_temp_high

    @property
    def target_temperature_low(self):
        return self._target_temp_low

    def __init__(self, hass, name, base_url, proxy_id, timeout):
        self._state = STATE_OFF
        self._operation = STATE_IDLE
        self.hass = hass
        self._name = name
        self._base_url = base_url;
        self._proxy_id = proxy_id;
        self._timeout = timeout
        self._current_temp = 0
       # self._target_temp_high = 0
        self._target_temp = 0
        self._unit = TEMP_FAHRENHEIT
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_AUTO]

    @property
    def name(self):
        return self._name

    @property
    def temperature_unit(self):
        return self._unit

    @property
    def precision(self):
        return 1

    @property
    def current_temperature(self):
        return self._current_temp

    @property
    def current_operation(self):
        return self._operation

    @property
    def target_temperature_high(self):
        return self._target_temp_high

    @property
    def target_temperature_low(self):
        return self._target_temp_low

    def __init__(self, hass, name, base_url, proxy_id, timeout):
        self._state = STATE_OFF
        self._operation = STATE_IDLE
        self.hass = hass
        self._name = name
        self._base_url = base_url;
        self._proxy_id = proxy_id;
        self._timeout = timeout
        self._current_temp = 0
        #self._target_temp_high = 0
        self._target_temp = 0
        self._unit = TEMP_FAHRENHEIT
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_AUTO]

    @property
    def name(self):
        return self._name

    @property
    def temperature_unit(self):
        return self._unit

    @property
    def precision(self):
        return 1

    @property
    def current_temperature(self):
        return self._current_temp

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._operation

    #@property
    #def target_temperature_high(self):
    #    return self._target_temp_high

    @property
    def target_temperature(self):
        return self._target_temp

    def set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        run_coroutine_threadsafe(self.update_state(TARGET_TEMP_LOW_VARIABLE_ID, temperature), self.hass.loop).result()
        self._target_temp = temperature
        #else:
        #    run_coroutine_threadsafe(self.update_state(TARGET_TEMP_HIGH_VARIABLE_ID, int(kwargs['target_temp_high'])), self.hass.loop).result()
        #    self._target_temp_high = int(kwargs['target_temp_high'])

    def set_operation_mode(self, operation_mode):
        run_coroutine_threadsafe(self.update_state(OPERATION_VARIABLE_ID, operation_mode),
                                 self.hass.loop).result()
        self._operation_mode = operation_mode

    def get_url(self, url, params):
        url_parts = list(urlparse.urlparse(url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query)

        return urlparse.urlunparse(url_parts)

    @asyncio.coroutine
    def update_state(self, variable_id, value):
        params = {
            'command': 'set',
            'proxyID': self._proxy_id,
            'variableID': variable_id,
            'newValue': value
        }

        websession = async_get_clientsession(self.hass)
        request = None
        try:
            with async_timeout.timeout(self._timeout, loop=self.hass.loop):
                request = yield from websession.get(self.get_url(self._base_url, params))
                _LOGGER.debug(params)
        except (asyncio.TimeoutError, aiohttp.errors.ClientError):
            _LOGGER.error("Error while turn on %s", self._base_url)
            return
        finally:
            if request is not None:
                yield from request.release()

        if request.status != 200:
            _LOGGER.error("Can't turn on %s. Is resource/endpoint offline?",
                          self._base_url)

    @asyncio.coroutine
    def async_update(self):
        """Get the latest data from API and update the state."""
        params = {
            'command': 'get',
            'proxyID': self._proxy_id,
            'variableID': ','.join([STATE_VARIABLE_ID, OPERATION_VARIABLE_ID,
                CURRENT_TEMP_VARIABLE_ID, UNIT_VARIABLE_ID, TARGET_TEMP_HIGH_VARIABLE_ID,
                TARGET_TEMP_LOW_VARIABLE_ID])
        }
        url = self.get_url(self._base_url, params)

        websession = async_get_clientsession(self.hass)
        request = None

        try:
            with async_timeout.timeout(self._timeout, loop=self.hass.loop):
                request = yield from websession.get(url)
                text = yield from request.text()
        except (asyncio.TimeoutError, aiohttp.errors.ClientError):
            _LOGGER.exception("Error while fetch data.")
            return
        finally:
            if request is not None:
                yield from request.release()
        json_text = json.loads(text)

        try:
            self._state = STATE_MAPPING[json_text[STATE_VARIABLE_ID]]
            self._operation = OPERATION_MAPPING[json_text[OPERATION_VARIABLE_ID]]
            self._current_temp = int(json_text[CURRENT_TEMP_VARIABLE_ID])
            #self._target_temp_high = int(json_text[TARGET_TEMP_HIGH_VARIABLE_ID])
            self._target_temp = int(json_text[TARGET_TEMP_LOW_VARIABLE_ID])
            self._unit = UNIT_MAPPING[json_text[UNIT_VARIABLE_ID]]
        except ValueError:
            _LOGGER.warning('Invalid value received')
