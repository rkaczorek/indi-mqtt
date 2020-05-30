# indi-mqtt
MQTT publisher for INDI server

# Installation
To install indi-mqtt using apt you need to add repository available on https://www.astroberry.io/
Then run the following commands:
```
sudo apt update
sudo apt install python-setuptools python-dev libindi-dev swig libcfitsio-dev libnova-dev
sudo apt install --no-install-recommends indi-mqtt
```
Note: If you want to install mosquitto server along indi-mqtt remove --no-install-recommends from the command line above

# Configuration
Default configuration file for indi-mqtt is located in /etc/indi-mqtt.conf

# MQTT tree
MQTT messages published by indi-mqtt are organized in the following hierarchy:\
__observatory/__#\
observatory/__status__ - observatory status (ON|OFF) - equals INDI server status\
observatory/__json__ - all INDI properties in a single JSON message\
observatory/__general/__#\
observatory/__telescope/__#\
observatory/__ccd/__#\
observatory/__guider/__#\
observatory/__focuser/__#\
observatory/__filter/__#\
observatory/__dome/__#\
observatory/__gps/__#\
observatory/__weather/__#\
observatory/__ao/__#\
observatory/__dustcap/__#\
observatory/__lighbox/__#\
observatory/__detector/__#\
observatory/__rotator/__#\
observatory/__spectrograph/__#\
observatory/__aux/__#

You can change 'observatory' by setting MQTT_ROOT in /etc/indi-mqtt.conf or invoking command with --mqtt_root argument.\
__\#__ is a wildcard selector, which returns all properties subsequent to path. If you want to access specific property, use full topic path e.g. ```observatory/telescope/telescope_info/telescope_focal_length``` will give you info about focal length of your telescope.\
You can list all available INDI properties by invoking ```python3 indi-mqtt.py --list_topics``` or ```python3 indi-mqtt.py -l``` for short.
JSON output is available if you set MQTT_JSON=True or by invoking ```python3 indi-mqtt.py --mqtt_json``` or ```python3 indi-mqtt.py -j``` for short.

# INDI properties polling
INDI properties can be refreshed in two modes:
- __Auto refresh__ with time configurable by MQTT_POLLING variable in /etc/indi-mqtt.conf or invoking command with --mqtt_polling argument
- __Manual refresh__ by publishing any message to MQTT_ROOT/poll topic (by default it is observatory/poll)

In both modes __all__ INDI properties are returned on poll. If you want to get a specific INDI property, subscribe to it using full topic path e.g. ```observatory/telescope/telescope_info/telescope_focal_length```

# Help
To get help run ```python3 /usr/bin/indi-mqtt.py --help``` or ```python3 /usr/bin/indi-mqtt.py -h``` for short

# FAQ
**Q: I'm not using Astroberry but want to use indi-mqtt. Can I?**

A: Yes you can. Download a package from https://www.astroberry.io/repo/pool/main/i/indi-mqtt/ and install it manually with sudo dpkg -i indi-mqtt_1.0.x_all.deb

# Issues
File any issues on https://github.com/rkaczorek/indi-mqtt/issues

