# indi-mqtt
MQTT publisher for INDI server

# Installation
Install pyindi-client **before** installing indi-mqtt
Normally it is installed as part of indi-mqtt installation from astroberry.io repository
However pyindi-client installable by pip contains error, which hopefully will be removed
soon. In the meantime you can install pyindi-client by running:
```
wget https://files.pythonhosted.org/packages/a7/4d/9ae15f572822c2fac5d6756570b205bdf578c80be24e274947ac74962873/pyindi-client-0.2.3.tar.gz
tar zxvf pyindi-client-0.2.3.tar.gz
cd pyindi-client
sudo python3 setup.py install
```

after you're done with pyindi-client installation, you are free to run:
```
sudo apt update
sudo apt install --no-install-recommends indi-mqtt
```

Note 1: To install indi-mqtt with apt you need to add repository available on https://www.astroberry.io/
Note 2: If you want to install mosquitto server along indi-mqtt remove --no-install-recommends from the command line above

# Configuration
Configuration file for indi-mqtt is located in /etc/indi-mqtt.conf

# Help
To get help run: python3 /usr/bin/indi-mqtt -h

# Issues
File any issues on https://github.com/rkaczorek/indi-mqtt/issues

