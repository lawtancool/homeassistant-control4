"""
Support for Control4 Alarm. You need to use control4-2way-web-driver
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

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_TIMEOUT, STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME, STATE_ALARM_DISARMED)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template
from homeassistant.util.async_ import run_callback_threadsafe
from homeassistant.util.async_ import run_coroutine_threadsafe
import homeassistant.util.dt as dt_util

CONF_BASE_URL = 'base_url'
CONF_PROXY_ID = 'proxy_id'
CONF_USE_V2 = 'use_v2'

DEFAULT_NAME = 'Control4 Alarm'
DEFAULT_TIMEOUT = 10
#STATE_VARIABLE_ID = '1104'
DISARMED_VARIABLE_ID = '1002'
ARMED_HOME_VARIABLE_ID = '1000'
ARMED_AWAY_VARIABLE_ID = '1001'
USE_V2_VARIABLE_ID = '1012'


SUPPORTED_STATES = [STATE_ALARM_DISARMED, STATE_ALARM_ARMED_AWAY,
                    STATE_ALARM_ARMED_HOME]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_BASE_URL): cv.url,
    vol.Required(CONF_PROXY_ID): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_USE_V2, default=DEFAULT_TIMEOUT): cv.boolean,
})

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument,
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    base_url = config.get(CONF_BASE_URL)
    proxy_id = config.get(CONF_PROXY_ID)
    timeout = config.get(CONF_TIMEOUT)
    use_v2 = config.get(CONF_USE_V2)

    yield from async_add_devices(
        [C4AlarmControlPanel(hass, name, base_url, proxy_id, timeout, use_v2)])

class C4AlarmControlPanel(alarm.AlarmControlPanel):

    def __init__(self, hass, name, base_url, proxy_id, timeout, use_v2):
        self._state = STATE_ALARM_DISARMED
        self.hass = hass
        self._name = name
        self._base_url = base_url
        self._proxy_id = proxy_id
        self._use_v2 = use_v2
        self._timeout = timeout
        self._disarmed = 0
        self._armedhome = 0
        self._armedaway = 0

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        if self._disarmed == "1":
            return STATE_ALARM_DISARMED
        elif self._armedhome == "1":
            return STATE_ALARM_ARMED_HOME
        elif self._armedaway == "1":
            return STATE_ALARM_ARMED_AWAY
        else:
            _LOGGER.error("Alarm state invalid!")

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
                _LOGGER.info(params)
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
        if self._use_v2:
          params = {
              'command': 'get',
              'proxyID': self._proxy_id,
              'variableID': ','.join([USE_V2_VARIABLE_ID])
          }
        else:
          params = {
              'command': 'get',
              'proxyID': self._proxy_id,
              'variableID': ','.join([DISARMED_VARIABLE_ID, ARMED_HOME_VARIABLE_ID, ARMED_AWAY_VARIABLE_ID])
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
        if self._use_v2:
          if json_text[USE_V2_VARIABLE_ID] == "Away":
            self._disarmed = 0
            self._armedhome = 0
            self._armedaway = 1
          elif json_text[USE_V2_VARIABLE_ID] == "Home":       
            self._disarmed = 0
            self._armedhome = 1
            self._armedaway = 0
          elif json_text[USE_V2_VARIABLE_ID] == "Disarmed":       
            self._disarmed = 1
            self._armedhome = 0
            self._armedaway = 0
          else:
            _LOGGER.warning('Invalid value received')
        else:
          try:
              self._disarmed = json_text[DISARMED_VARIABLE_ID]
              self._armedhome = json_text[ARMED_HOME_VARIABLE_ID]
              self._armedaway = json_text[ARMED_AWAY_VARIABLE_ID]
          except ValueError:
              _LOGGER.warning('Invalid value received')
