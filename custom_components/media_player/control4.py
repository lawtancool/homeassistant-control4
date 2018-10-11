"""
Support for Control4 Media. You need to use control4-2way-web-driver
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

from homeassistant.components.media_player import (
    DOMAIN, MEDIA_PLAYER_SCHEMA, PLATFORM_SCHEMA, SUPPORT_VOLUME_SET, MediaPlayerDevice)
from homeassistant.const import (CONF_NAME, CONF_RESOURCE, CONF_TIMEOUT)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template
from homeassistant.util.async_ import run_callback_threadsafe
from homeassistant.util.async_ import run_coroutine_threadsafe

CONF_BASE_URL = 'base_url'
CONF_PROXY_ID = 'proxy_id'
CONF_OUTPUT_ZONE = 'output_zone'

DEFAULT_NAME = 'Control4 Media'
DEFAULT_TIMEOUT = 10
STATE_VARIABLE_ID = '1000'
VOLUME_VARIABLE_ID = '1011'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_BASE_URL): cv.url,
    vol.Required(CONF_PROXY_ID): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (SUPPORT_VOLUME_SET)

# pylint: disable=unused-argument,
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    base_url = config.get(CONF_BASE_URL)
    proxy_id = config.get(CONF_PROXY_ID)
    timeout = config.get(CONF_TIMEOUT)
    #output_zone = config.get(CONF_OUTPUT_ZONE)

    yield from async_add_devices(
        [C4Media(hass, name, base_url, proxy_id, timeout)])

class C4Media(MediaPlayerDevice):

    def __init__(self, hass, name, base_url, proxy_id, timeout):
        self._state = None
        self._volume = 0
        self.hass = hass
        self._name = name
        self._base_url = base_url;
        self._proxy_id = proxy_id;
        self._timeout = timeout
       # VOLUME_VARIABLE_ID = int(1900 + (output_zone - 1))

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

#    @property
#    def is_on(self):
#        return self._state

    @property
    def volume_level(self):
        return self._volume

   # @asyncio.coroutine
    def set_volume_level(self, volume):
        VOLUME_REAL = int(volume*100)
        run_coroutine_threadsafe(self.update_state(VOLUME_VARIABLE_ID, VOLUME_REAL), self.hass.loop).result()

        VOLUME_REAL_STRING = str(VOLUME_REAL)
        VOLUME_VARIABLE_ID_STRING = str(VOLUME_VARIABLE_ID)
        _LOGGER.debug(VOLUME_REAL_STRING)
        self._volume = volume

#    @asyncio.coroutine
#    def async_turn_off(self, **kwargs):
#        yield from self.update_state(STATE_VARIABLE_ID, 0)
#        self._state = False

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
        _LOGGER.debug("Reached update_state")
        websession = async_get_clientsession(self.hass)
        request = None
        try:
            with async_timeout.timeout(self._timeout, loop=self.hass.loop):
                _LOGGER.debug(params)
                request = yield from websession.get(self.get_url(self._base_url, params))
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
            'variableID': ','.join([STATE_VARIABLE_ID, VOLUME_VARIABLE_ID])
        }
        url = self.get_url(self._base_url, params)

        websession = async_get_clientsession(self.hass)
        request = None

        try:
            with async_timeout.timeout(self._timeout, loop=self.hass.loop):
                _LOGGER.debug(params)
                request = yield from websession.get(url)
                text = yield from request.text()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.exception("Error while fetch data.")
            return
        finally:
            if request is not None:
                yield from request.release()
        json_text = json.loads(text)

        #is_on = json_text[STATE_VARIABLE_ID]
        #if is_on == '1':
        #    self._state = True
        #elif is_on == '0':
        #    self._state = False
        #else:
        #    self._state = None
        self._state = json_text[STATE_VARIABLE_ID]
        self._volume = float(json_text[VOLUME_VARIABLE_ID]) / 100

        #try:
        #    self._brightness = int(int(brightness)*255/100)
        #except ValueError:
        #    _LOGGER.warning('Invalid brightness value received')
