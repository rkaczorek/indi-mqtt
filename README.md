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
observatory/__status__ - obervatory status (ON|OFF) - equals INDI server status\
observatory/__json__ - all INDI properties in a single json message\
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
__\#__ is a wildcard selector, which returns all properties subsequent to path. If you want to access specific property, use full path e.g. ```observatory/telescope/telescope_info/telescope_focal_length``` will give you info about focal length of your telescope.

# Help
To get help run:
```
python3 /usr/bin/indi-mqtt.py -h
```

# FAQ
**Q: I'm not using Astroberry but want to use indi-mqtt. Can I?**

A: Yes you can. Download a package from https://www.astroberry.io/repo/pool/main/i/indi-mqtt/ and install it manually with sudo dpkg -i indi-mqtt_1.0.0_all.deb

# Issues
File any issues on https://github.com/rkaczorek/indi-mqtt/issues

