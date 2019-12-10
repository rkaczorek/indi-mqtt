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

