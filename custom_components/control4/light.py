"""
Support for Control4 Lights. You need to use control4-2way-web-driver
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

from homeassistant.components.light import (ATTR_BRIGHTNESS, Light, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_RESOURCE, CONF_TIMEOUT)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template

CONF_BASE_URL = 'base_url'
CONF_PROXY_ID = 'proxy_id'

DEFAULT_NAME = 'Control4 Light'
DEFAULT_TIMEOUT = 10
STATE_VARIABLE_ID = '1000'
BRIGHTNESS_VARIABLE_ID = '1001'

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
        [C4Light(hass, name, base_url, proxy_id, timeout)])

class C4Light(Light):

    def __init__(self, hass, name, base_url, proxy_id, timeout):
        self._state = None
        self._brightness = 0
        self.hass = hass
        self._name = name
        self._base_url = base_url;
        self._proxy_id = proxy_id;
        self._timeout = timeout

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def brightness(self):
        return self._brightness

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        if 'brightness' in kwargs:
            yield from self.update_state(BRIGHTNESS_VARIABLE_ID, int(kwargs['brightness'] * 100 / 255))
            self._brightness = kwargs['brightness']
        else:
            yield from self.update_state(STATE_VARIABLE_ID, 1)
            self._state = True
            self._brightness = 255

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        yield from self.update_state(STATE_VARIABLE_ID, 0)
        self._state = False

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
            'variableID': ','.join([STATE_VARIABLE_ID, BRIGHTNESS_VARIABLE_ID])
        }
        url = self.get_url(self._base_url, params)

        websession = async_get_clientsession(self.hass)
        request = None

        try:
            with async_timeout.timeout(self._timeout, loop=self.hass.loop):
                request = yield from websession.get(url)
                text = yield from request.text()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.exception("Error while fetch data.")
            return
        finally:
            if request is not None:
                yield from request.release()
        json_text = json.loads(text)

        is_on = json_text[STATE_VARIABLE_ID]
        if is_on == '1':
            self._state = True
        elif is_on == '0':
            self._state = False
        else:
            self._state = None

        brightness = json_text[BRIGHTNESS_VARIABLE_ID]

        try:
            self._brightness = int(int(brightness)*255/100)
        except ValueError:
            _LOGGER.warning('Invalid brightness value received')
