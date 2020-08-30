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
import asyncio

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_DRY,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
    SUPPORT_TARGET_HUMIDITY
)
from homeassistant.const import (
    CONF_NAME,
    CONF_TIMEOUT,
    TEMP_FAHRENHEIT,
    TEMP_CELSIUS,
    ATTR_TEMPERATURE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template

TIMEOUT = 10

CONF_BASE_URL = 'base_url'
CONF_PROXY_ID = 'proxy_id'
CONF_WEB_TWO_WAY_PORT = 'web_two_way_port'
CONF_WEB_EVENT_PORT = 'web_event_port'
CONF_DEHUMIDIFY = 'dehumidify'

DEFAULT_NAME = 'Control4 Thermostat'
DEFAULT_WEB_TWO_WAY_PORT = 9000
DEFAULT_WEB_EVENT_PORT = 8080
DEFAULT_TIMEOUT = 10

STATE_VARIABLE_ID = '1107'
HUMIDITY_STATE_VARIABLE_ID = '1141'
MODE_VARIABLE_ID = '1104'
HUMIDITY_MODE_VARIABLE_ID = '1139'
CURRENT_TEMP_VARIABLE_ID = '1130'
CURRENT_HUMIDITY_VARIABLE_ID = '1138'
#UNIT_VARIABLE_ID = '1100'
TARGET_TEMP_HIGH_VARIABLE_ID = '1134'
TARGET_TEMP_LOW_VARIABLE_ID = '1132'
TARGET_HUMIDITY_VARIABLE_ID = '1143'
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE_RANGE | SUPPORT_TARGET_TEMPERATURE)

MODE_MAPPING = {
    "Off": HVAC_MODE_OFF,
    "Cool": HVAC_MODE_COOL,
    "Heat": HVAC_MODE_HEAT,
    "Auto": HVAC_MODE_HEAT_COOL
}

HUMIDITY_MODE_MAPPING = {
    "Off": HVAC_MODE_OFF,
    "Dehumidify": HVAC_MODE_DRY
}

STATE_MAPPING = {
    "Off": CURRENT_HVAC_IDLE,
    "" : CURRENT_HVAC_IDLE,
    "Cool": CURRENT_HVAC_COOL,
    "Stage 1 Cool": CURRENT_HVAC_COOL,
    "Stage 1 and 2 Cool": CURRENT_HVAC_COOL,
    "Heat": CURRENT_HVAC_HEAT
}

HUMIDITY_STATE_MAPPING = {
    "Off": CURRENT_HVAC_IDLE,
    "Dehumidifying Equipment Wait" : CURRENT_HVAC_DRY
}

UNIT_MAPPING = {
    "FAHRENHEIT": TEMP_FAHRENHEIT,
    "CELSIUS": TEMP_CELSIUS
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_BASE_URL): cv.url,
    vol.Required(CONF_PROXY_ID): cv.positive_int,
    vol.Optional(CONF_WEB_TWO_WAY_PORT, default=DEFAULT_WEB_TWO_WAY_PORT): cv.positive_int,
    vol.Optional(CONF_WEB_EVENT_PORT, default=DEFAULT_WEB_EVENT_PORT): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_DEHUMIDIFY, default=False): cv.boolean
})

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    base_url = config.get(CONF_BASE_URL) + ':' + str(config.get(CONF_WEB_TWO_WAY_PORT)) + '/'
    event_url = config.get(CONF_BASE_URL) + ':' + str(config.get(CONF_WEB_EVENT_PORT)) + '/'
    proxy_id = config.get(CONF_PROXY_ID)
    timeout = config.get(CONF_TIMEOUT)
    dehumidify = config.get(CONF_DEHUMIDIFY)

    async_add_devices([C4ClimateDevice(hass, name, base_url, proxy_id, timeout,
        event_url, dehumidify)])

class C4ClimateDevice(ClimateEntity):

    def __init__(self, hass, name, base_url, proxy_id, timeout, event_url,
            dehumidify):
        self._state = CURRENT_HVAC_IDLE
        self._humidity_state = CURRENT_HVAC_IDLE
        self._hvac_mode = HVAC_MODE_OFF
        self._humidity_hvac_mode = HVAC_MODE_OFF
        self.hass = hass
        self._name = name
        self._base_url = base_url;
        self._event_url = event_url;
        self._proxy_id = proxy_id;
        self._timeout = timeout
        self._current_temp = 0
        self._current_humidity = 0
        self._target_temp_high = 0
        self._target_temp_low = 0
        self._target_temp = 0
        self._target_humidity = 0
        self._unit = TEMP_FAHRENHEIT
        self._dehumidify = dehumidify
        self._hvac_modes = [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL,
                            HVAC_MODE_HEAT_COOL]
        if self._dehumidify:
            self._hvac_modes.append(HVAC_MODE_DRY)

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        support_flags = 0
        if self._hvac_mode == HVAC_MODE_HEAT or self._hvac_mode == HVAC_MODE_COOL or self._humidity_hvac_mode == HVAC_MODE_DRY:
          support_flags = support_flags | SUPPORT_TARGET_TEMPERATURE
        elif self._hvac_mode == HVAC_MODE_HEAT_COOL:
          support_flags = support_flags | SUPPORT_TARGET_TEMPERATURE_RANGE
        else:
          support_flags = support_flags | SUPPORT_TARGET_TEMPERATURE_RANGE
        if self._dehumidify:
          support_flags = support_flags | SUPPORT_TARGET_HUMIDITY
        return support_flags

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return self._hvac_modes

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
    def target_temperature(self):
        return self._target_temp

    @property
    def hvac_mode(self):
        if self._dehumidify and self._hvac_mode == HVAC_MODE_OFF:
          return self._humidity_hvac_mode
        return self._hvac_mode

    @property
    def precision(self):
        return 1

    @property
    def hvac_action(self):
        if self._dehumidify and self._state == CURRENT_HVAC_IDLE:
          return self._humidity_state
        return self._state

    @property
    def target_temperature_high(self):
        return self._target_temp_high

    @property
    def target_temperature_low(self):
        return self._target_temp_low

    @property
    def current_humidity(self):
        return self._current_humidity

    @property
    def target_humidity(self):
        return self._target_humidity

    def set_temperature(self, **kwargs):
        temp_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        temp_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        single_temp = kwargs.get(ATTR_TEMPERATURE)

        if single_temp is not None:
          _LOGGER.debug('Single Temp Update Mode: ' + str(single_temp))
          if self._hvac_mode == HVAC_MODE_HEAT:
            asyncio.run_coroutine_threadsafe(self.update_state(TARGET_TEMP_LOW_VARIABLE_ID, int(single_temp)), self.hass.loop).result()
            self._target_temp = single_temp
          elif self._hvac_mode == HVAC_MODE_COOL:
            asyncio.run_coroutine_threadsafe(self.update_state(TARGET_TEMP_HIGH_VARIABLE_ID, int(single_temp)), self.hass.loop).result()
            self._target_temp = single_temp
        elif temp_low != 0 and temp_high != 0:
          _LOGGER.debug('Dual Update Mode: ' + str(temp_low) + ' to ' + str(temp_high))
          asyncio.run_coroutine_threadsafe(self.update_state(TARGET_TEMP_LOW_VARIABLE_ID, int(temp_low)), self.hass.loop).result()
          self._target_temp_low = temp_low
          asyncio.run_coroutine_threadsafe(self.update_state(TARGET_TEMP_HIGH_VARIABLE_ID, int(temp_high)), self.hass.loop).result()
          self._target_temp_high = temp_high
        else:
          _LOGGER.warning('Invalid Temperature Values Passed to Update Method.')
          return

    def set_humidity(self, humidity):
        _LOGGER.debug('Humidity Update Mode: ' + str(humidity))
        asyncio.run_coroutine_threadsafe(self.update_state(TARGET_HUMIDITY_VARIABLE_ID, int(humidity)), self.hass.loop).result()
        self._target_humidity = humidity

# The following method is broken with the 2 way web driver, I've implemented the web event
# driver, and programming in COntrol4 to work around this. The 2-way web driver cannot update
# the HVAC mode in control4, it appears to be an underlying issue with LUA
#    def set_hvac_mode(self, hvac_mode):
#        asyncio.run_coroutine_threadsafe(self.update_state(MODE_VARIABLE_ID, hvac_mode),
#                                 self.hass.loop).result()
#        self._hvac_mode = hvac_mode

#This method uses the Web event driver to issue commands to Control4 to change the HVAC Mode
#Additional programming in the C4 director is needed to handle the commands and adjust the HVAC Mode
    @asyncio.coroutine
    def async_set_hvac_mode(self, hvac_mode):
      url_str = self._event_url
      if hvac_mode == HVAC_MODE_HEAT:
        self._current_operation = HVAC_MODE_HEAT
        self._enabled = True
        url_str = url_str + 'Heat'
      elif hvac_mode == HVAC_MODE_COOL:
        self._current_operation = HVAC_MODE_COOL
        self._enabled = True
        url_str = url_str + 'Cool'
      elif hvac_mode == HVAC_MODE_HEAT_COOL:
        self._current_operation = HVAC_MODE_HEAT_COOL
        self._enabled = True
        url_str = url_str + 'Auto'
      elif hvac_mode == HVAC_MODE_OFF:
        self._current_operation = HVAC_MODE_OFF
        self._enabled = False
        url_str = url_str + 'Off'

      try:
        websession = async_get_clientsession(self.hass)
        request = None
        with async_timeout.timeout(TIMEOUT, loop=self.hass.loop):
          request = yield from websession.get(url_str)
        return
      except:
        _LOGGER.warning('Web Event driver on Control4 Controller is not responding. Please Install the Web Event driver in order to control HVAC Mode')
        return


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
            'variableID': ','.join([STATE_VARIABLE_ID,
                HUMIDITY_STATE_VARIABLE_ID, MODE_VARIABLE_ID,
                HUMIDITY_MODE_VARIABLE_ID, CURRENT_TEMP_VARIABLE_ID,
                CURRENT_HUMIDITY_VARIABLE_ID, TARGET_TEMP_HIGH_VARIABLE_ID,
                TARGET_TEMP_LOW_VARIABLE_ID, TARGET_HUMIDITY_VARIABLE_ID])
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
            self._humidity_state = HUMIDITY_STATE_MAPPING[json_text[HUMIDITY_STATE_VARIABLE_ID]]
            self._hvac_mode = MODE_MAPPING[json_text[MODE_VARIABLE_ID]]
            self._humidity_hvac_mode = HUMIDITY_MODE_MAPPING[json_text[HUMIDITY_MODE_VARIABLE_ID]]
            self._current_temp = int(json_text[CURRENT_TEMP_VARIABLE_ID])
            self._current_humidity = int(json_text[CURRENT_HUMIDITY_VARIABLE_ID])
            self._target_temp_high = int(json_text[TARGET_TEMP_HIGH_VARIABLE_ID])
            self._target_temp_low = int(json_text[TARGET_TEMP_LOW_VARIABLE_ID])
           # self._unit = UNIT_MAPPING[json_text[UNIT_VARIABLE_ID]]
            
            if self._hvac_mode == HVAC_MODE_HEAT:
              self._target_temp = int(json_text[TARGET_TEMP_LOW_VARIABLE_ID])
            elif self._hvac_mode == HVAC_MODE_COOL:
              self._target_temp = int(json_text[TARGET_TEMP_HIGH_VARIABLE_ID])
            elif self._humidity_hvac_mode == HVAC_MODE_DRY:
              self._target_temp = int(json_text[TARGET_TEMP_HIGH_VARIABLE_ID])
            else:
              self._target_temp = 0

            if self._humidity_hvac_mode == HVAC_MODE_DRY:
              self._target_humidity = int(json_text[TARGET_HUMIDITY_VARIABLE_ID])
            else:
              self._target_humidity = 0

        except ValueError:
            _LOGGER.warning('Invalid value received')
