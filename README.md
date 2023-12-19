# homeassistant-control4
> [!WARNING]
> This integration is no longer maintained and is likely broken on newer versions of Home Assistant.
>
> Consider migrating to https://github.com/lawtancool/hass-control4, which is faster, supports the latest Home Assistant releases, and does not require a custom driver to be installed on the Control4 system. 

These custom components for Home Assistant (https://www.home-assistant.io) allow you to integrate Control4 systems into Home Assistant. Currently, lights, thermostats, alarm systems, and media room volume control are supported. 

How to use:
-------------
- Install the Web2Way driver into your Control4 project using Composer Pro (2.9+ recommended): https://github.com/itsfrosty/control4-2way-web-driver (You may need your dealer to do this if you don't have access to the Control4 Composer Pro program)
- Copy the custom_components into your ~/.homeassistant/ folder
- Find the `proxy_id` of each Control4 device you want to integrate inside Composer Pro, and include them in your `configuration.yaml`
- **NOTE**: If you have a lot of Control4 devices and you are experiencing large delays in executing actions, try randomizing your `scan_interval`, setting different devices to slightly different values; this should help prevent Home Assistant from overwhelming the Control4 controller with refresh requests. However, don't set this value too high, otherwise Control4 state changes will take a long time to be reflected inside Home Assistant.

Sample Home Assistant `configuration.yaml` entries:
-------
~~~~
base_url: The IP address of your Control4 controller + ":9000". (You should assign a static IP to your controller on your router)
proxy_id: The proxy ID of the Control4 device, found inside Composer Pro by hovering over the device in the project tree view.
name: The name that Home Assistant will use to identify the device.
scan_interval: How often to query the Control4 controller about the state of the device, in seconds.
~~~~

**Lights:**
~~~~
light:
  - platform: control4
    base_url: 'http://192.168.1.20:9000/'
    proxy_id: 14
    name: Piano Room
    scan_interval: 10
~~~~
**Thermostats:**
~~~~
climate:
  - platform: control4
    base_url: 'http://192.168.1.20:9000/'
    proxy_id: 220
    name: Downstairs
    scan_interval: 20
~~~~
**Alarm System:**
~~~~
alarm_control_panel:
  - platform: control4
    base_url: 'http://192.168.1.20:9000'
    proxy_id: 70
    name: DSC Alarm
    scan_interval: 10
~~~~
**Media volume control:**
(The `proxy_id` needs to be the ID of the room inside Composer Pro)
~~~~
media_player:
  - platform: control4
    base_url: 'http://192.168.1.20:9000'
    proxy_id: 8
    name: Kitchen Speakers
    scan_interval: 10
~~~~

Acknowledgements:
------
This is heavily based on work by itsfrosty: https://github.com/itsfrosty/homeassistant-control4
