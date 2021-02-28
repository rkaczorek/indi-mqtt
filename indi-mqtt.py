#!/usr/bin/env python3
# coding=utf-8

"""
Copyright(c) 2019 Radek Kaczorek  <rkaczorek AT gmail DOT com>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Library General Public
License version 3 as published by the Free Software Foundation.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Library General Public License for more details.

You should have received a copy of the GNU Library General Public License
along with this library; see the file COPYING.LIB.  If not, write to
the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301, USA.
"""

import os, sys, time, logging, configparser
import PyIndi
import paho.mqtt.client as mqtt
import signal
import json
import argparse
import random
import string

__author__ = 'Radek Kaczorek'
__copyright__ = 'Copyright 2019-2020, Radek Kaczorek'
__license__ = 'GPL-3'
__version__ = '1.0.6'

# Default options
LOG_LEVEL = logging.INFO
LIST_TOPICS = False
CONFIG_FILE = "/etc/indi-mqtt.conf"

# INDI
INDI_HOST = 'localhost'
INDI_PORT = 7624

# MQTT
MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASS = None
MQTT_ROOT = 'observatory'
MQTT_POLLING = 10
MQTT_JSON = False

# Init logging
logger = logging.getLogger('indi-mqtt')
logging.basicConfig(format='%(name)s: %(message)s', level=LOG_LEVEL, stream=sys.stdout)

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="configuration file path (default = /etc/indi-mqtt.conf)")
parser.add_argument("--log_level", help="logging level (default = info)")
parser.add_argument("-l", "--list_topics", help="list available MQTT topics", action="store_true")
parser.add_argument("-j", "--mqtt_json", help="enable full json on MQTT root/json", action="store_true")
parser.add_argument("--indi_host", help="INDI server hostname or IP (default = localhost)")
parser.add_argument("--indi_port", help="INDI server port number (default = 7624)")
parser.add_argument("--mqtt_host", help="MQTT server hostname or IP (default = localhost)")
parser.add_argument("--mqtt_port", help="MQTT server port number (default = 1883)")
parser.add_argument("--mqtt_user", help="MQTT server username (default = none)")
parser.add_argument("--mqtt_pass", help="MQTT server password (default = none)")
parser.add_argument("--mqtt_root", help="MQTT root topic name (default = observatory)")
parser.add_argument("--mqtt_polling", help="MQTT polling time in seconds (default = 10)")
args = parser.parse_args()

if args.config:
	CONFIG_FILE = args.config

if os.path.isfile(CONFIG_FILE):
		config = configparser.ConfigParser()
		config.read(CONFIG_FILE)
		logger.info("Using configuration from " + CONFIG_FILE)

		if 'LOG_LEVEL' in config['DEFAULT']:
			if config['DEFAULT']['LOG_LEVEL'].lower() == 'info':
				LOG_LEVEL = logging.INFO
			if config['DEFAULT']['LOG_LEVEL'].lower() == 'debug':
				LOG_LEVEL = logging.DEBUG
			if config['DEFAULT']['LOG_LEVEL'].lower() == 'warning':
				LOG_LEVEL = logging.WARNING
			if config['DEFAULT']['LOG_LEVEL'].lower() == 'error':
				LOG_LEVEL = logging.ERROR
			if config['DEFAULT']['LOG_LEVEL'].lower() == 'critical':
				LOG_LEVEL = logging.CRITICAL
		if 'INDI_HOST' in config['INDI']:
			INDI_HOST = config['INDI']['INDI_HOST']
		if 'INDI_PORT' in config['INDI']:
			INDI_PORT = int(config['INDI']['INDI_PORT'])
		if 'MQTT_HOST' in config['MQTT']:
			MQTT_HOST = config['MQTT']['MQTT_HOST']
		if 'MQTT_PORT' in config['MQTT']:
			MQTT_PORT = int(config['MQTT']['MQTT_PORT'])
		if 'MQTT_USER' in config['MQTT']:
			MQTT_USER = config['MQTT']['MQTT_USER']
		if 'MQTT_PASS' in config['MQTT']:
			MQTT_PASS = config['MQTT']['MQTT_PASS']
		if 'MQTT_ROOT' in config['MQTT']:
			MQTT_ROOT = config['MQTT']['MQTT_ROOT']
		if 'MQTT_POLLING' in config['MQTT']:
			MQTT_POLLING = int(config['MQTT']['MQTT_POLLING'])
		if 'MQTT_JSON' in config['MQTT']:
			if config['MQTT']['MQTT_JSON'].lower() == 'true':
				MQTT_JSON = True

if args.log_level:
	if args.log_level.lower() == 'info':
		LOG_LEVEL = logging.INFO
	if args.log_level.lower() == 'debug':
		LOG_LEVEL = logging.DEBUG
	if args.log_level.lower() == 'warning':
		LOG_LEVEL = logging.WARNING
	if args.log_level.lower() == 'error':
		LOG_LEVEL = logging.ERROR
	if args.log_level.lower() == 'critical':
		LOG_LEVEL = logging.CRITICAL

if args.list_topics:
	LIST_TOPICS = True
if args.indi_host:
	INDI_HOST = args.indi_host
if args.indi_port:
	INDI_PORT = int(args.indi_port)
if args.mqtt_host:
	MQTT_HOST = args.mqtt_host
if args.mqtt_port:
	MQTT_PORT = int(args.mqtt_port)
if args.mqtt_user:
	MQTT_USER = args.mqtt_user
if args.mqtt_pass:
	MQTT_PASS = args.mqtt_pass
if args.mqtt_root:
	MQTT_ROOT = args.mqtt_root
if args.mqtt_polling:
	MQTT_POLLING = int(args.mqtt_polling)
if args.mqtt_json:
	MQTT_JSON = True

# Set logging level
logger.setLevel(LOG_LEVEL)

# if user/pass available prepare auth data
if MQTT_USER and MQTT_PASS:
	MQTT_AUTH = {'username': MQTT_USER, 'password': MQTT_PASS}
else:
	MQTT_AUTH = None

# INDI states
def strISState(s):
	if (s == PyIndi.ISS_OFF):
		return "OFF"
	else:
		return "ON"

def strIPState(s):
	if (s == PyIndi.IPS_IDLE):
		return "IDLE"
	elif (s == PyIndi.IPS_OK):
		return "OK"
	elif (s == PyIndi.IPS_BUSY):
		return "BUSY"
	elif (s == PyIndi.IPS_ALERT):
		return "ALERT"

# https://www.indilib.org/api/classINDI_1_1BaseDevice.html#a9b946349e7f37be39e80221b8d7539f3
def strDeviceType(s):
	if s & 0:
		return "GENERAL"
	elif s & (1 << 0):
		return "TELESCOPE"
	elif s & (1 << 1):
		return "CCD"
	elif s & (1 << 2):
		return "GUIDER"
	elif s & (1 << 3):
		return "FOCUSER"
	elif s & (1 << 4):
		return "FILTER"
	elif s & (1 << 5):
		return "DOME"
	elif s & (1 << 6):
		return "GPS"
	elif s & (1 << 7):
		return "WEATHER"
	elif s & (1 << 8):
		return "AO"
	elif s & (1 << 9):
		return "DUSTCAP"
	elif s & (1 << 10):
		return "LIGHTBOX"
	elif s & (1 << 11):
		return "DETECTOR"
	elif s & (1 << 12):
		return "ROTATOR"
	elif s & (1 << 13):
		return "SPECTROGRAPH"
	elif s & (1 << 15):
		return "AUX"
	else:
		return "UNKNOWN"

def shutdown():
	indiclient.disconnectServer()
	mqttclient.disconnect()
	logger.info('Exiting\nGood Bye.\n')
	sys.exit()

def term_handler(signum, frame):
        raise KeyboardInterrupt

# The IndiClient class which inherits from the module PyIndi.BaseClient class
# It should implement all the new* pure virtual functions.
class IndiClient(PyIndi.BaseClient):
	def __init__(self):
		super(IndiClient, self).__init__()
		logger.info('Creating an instance of INDI client')
	def newDevice(self, d):
		pass
	def newProperty(self, p):
		pass
	def removeProperty(self, p):
		pass
	def newBLOB(self, bp):
		pass
	def newSwitch(self, svp):
		pass
	def newNumber(self, nvp):
		pass
	def newText(self, tvp):
		pass
	def newLight(self, lvp):
		pass
	def newMessage(self, d, m):
		pass
	def serverConnected(self):
		logger.info("Connected to INDI server " + self.getHost() + ":" + str(self.getPort()))
	def serverDisconnected(self, code):
		logger.info("Disconnected from INDI server " + str(self.getHost()) + ":" + str(self.getPort()))

def getJSON(devices):
	# Construct RFC 8259 compliant JSON
	# {
	#	device_type:	{device_name: {property:value,property:value}},
	#	device_type:	{
	#				device_name:{property:value,property:value},
	#				device_name:{property:value,property:value}
	#			}
	# }

	observatory_json = json.loads("{}")

	for device in devices:
		device_type = strDeviceType(device.getDriverInterface())
		device_name = "_".join( device.getDeviceName().split() ).upper()
		device_name_json = json.loads("{}")
		properties = device.getProperties()
		device_properties_json = json.loads("{}")

		for property in properties:
			device_property_json = json.loads("{}")
			property_name = property.getName()
			if property.getType() == PyIndi.INDI_TEXT:
				tpy = property.getText()
				for t in tpy:
					device_property_json.update({t.name:t.text})
					device_properties_json.update({property_name:device_property_json})
			elif property.getType()==PyIndi.INDI_NUMBER:
				tpy = property.getNumber()
				for t in tpy:
					device_property_json.update({t.name:t.value})
					device_properties_json.update({property_name:device_property_json})
			elif property.getType()==PyIndi.INDI_SWITCH:
				tpy = property.getSwitch()
				for t in tpy:
					device_property_json.update({t.name:strISState(t.s)})
					device_properties_json.update({property_name:device_property_json})
			elif property.getType()==PyIndi.INDI_LIGHT:
				tpy = property.getLight()
				for t in tpy:
					device_property_json.update({t.name:strIPState(t.s)})
					device_properties_json.update({property_name:device_property_json})
			elif property.getType()==PyIndi.INDI_BLOB:
				tpy = property.getBLOB()
				for t in tpy:
					device_property_json.update({t.name:'<blob ' + str(t.size) + ' bytes>'})
					device_properties_json.update({property_name:device_property_json})

		device_name_json.update({device_name:device_properties_json})

		# Handle multiple devices of a type
		if device_type in observatory_json.keys():
			existing_device_type_json = observatory_json[device_type]
			existing_device_type_json.update(device_name_json)
		else:
			observatory_json.update({device_type:device_name_json})

	logger.debug(json.dumps(observatory_json, indent=4, sort_keys=False))

	return observatory_json

def sendMQTT(observatory_json):
	try:
		# Publish entire json in json topic e.g. observatory/json
		if MQTT_JSON:
			msg = mqttclient.publish(MQTT_ROOT.lower() + "/json", json.dumps(observatory_json))

		# Publish each property in separate topic e.g. observatory/telescope/telescope_simulator/connection/connect
		for device_type in observatory_json:
			for device_name in observatory_json[device_type]:
				for property in observatory_json[device_type][device_name]:
					for key in observatory_json[device_type][device_name][property]:
						topic = MQTT_ROOT + '/' + device_type + '/' + device_name + '/' + property + '/' + key
						payload = observatory_json[device_type][device_name][property][key]
						if LIST_TOPICS:
							print(topic.lower())
							#print(topic.lower(), payload, sep=" = ")
						msg = mqttclient.publish(topic.lower(), payload)

		if msg.rc == 0:
			logger.debug("Message published to MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT))
		else:
			logger.error("Error publishing to MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT) + " (" + msg.rc + ")")
	except Exception as err:
		logger.error("Unexpected error publishing to MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT), err)

def ClientIdMQTT(stringLength=18):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))

def onConnectMQTT(client, userdata, flags, rc):
	if rc == 0:
		logger.info("Connected to MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT))

		# Subscribe to polling control
		mqttclient.subscribe(MQTT_ROOT.lower() + "/poll")
		mqttclient.message_callback_add(MQTT_ROOT.lower() + "/poll", onPollMQTT)
		logger.info("Subscribed to " + MQTT_ROOT.lower() + "/poll topic at MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT))

def onDisconnectMQTT(client, userdata, rc):
	if rc == 0:
		logger.info("Disconnected from MQTT server  " + MQTT_HOST + ":" + str(MQTT_PORT))
	if rc == 5:
		logger.warning("Access denied to MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT) + ". Check username and password") 
	else:
		logger.warning("Connection lost to MQTT server " + MQTT_HOST + ":" + str(MQTT_PORT))

def onPollMQTT(client, userdata, message):
	global MQTT_POLLING

	# Decode message to string
	msg = message.payload.decode("utf-8")

	logger.debug("Polling control message received: " + msg)

	# polling control
	if msg.isnumeric():
		if int(msg) > 0:
			MQTT_POLLING = int(msg)
			logger.info("Setting auto refresh mode to " + str(MQTT_POLLING) + " seconds")
		else:
			if int(msg) != MQTT_POLLING:
				logger.info("Setting manual refresh mode")
			MQTT_POLLING = 0
	else:
		logger.warning("Invalid polling control message")

	if indiclient.isServerConnected():
		# Set observatory status
		mqttclient.publish(MQTT_ROOT.lower() + "/status", "ON")
		try:
			# Get all devices
			devices = indiclient.getDevices()

			# Get properties and their associated values for all devices
			observatory_json = getJSON(devices)

			# Send MQTT message
			sendMQTT(observatory_json)
		except KeyboardInterrupt:
			shutdown()
		except Exception as err:
			logger.error("Unexpected error manual polling INDI server", err)
	else:
		# Set observatory status
		mqttclient.publish(MQTT_ROOT.lower() + "/status", "OFF")

# register term handler
signal.signal(signal.SIGTERM, term_handler)

if __name__ == '__main__':
	# Init message
	if MQTT_POLLING > 0:
		logger.info("Starting in auto refresh mode in every " + str(MQTT_POLLING) + " seconds.")
	else:
		logger.info("Starting in manual refresh mode. Publish a numeric value to " + MQTT_ROOT.lower() + "/poll to set refresh time in seconds.")

	# Create MQTT client instance
	mqttclientid = "indi-mqtt-" + ClientIdMQTT()
	mqttclient = mqtt.Client(client_id = mqttclientid, clean_session = True)
	logger.debug("Creating an instance of MQTT client")

	mqttclient.reconnect_delay_set(min_delay=1, max_delay=60)
	mqttclient.username_pw_set(MQTT_USER, MQTT_PASS)
	mqttclient.on_connect = onConnectMQTT
	mqttclient.on_disconnect = onDisconnectMQTT

	# Try connecting to MQTT server or loop until MQTT server is available
	while True:
		try:
			mqttclient.connect(MQTT_HOST, MQTT_PORT, 60)
			break
		except KeyboardInterrupt:
			shutdown()
		except:
			logger.debug("MQTT server at " + MQTT_HOST + ":" + str(MQTT_PORT) + " not available. Retrying in 10 seconds")
			time.sleep(10)
			continue

	# Start mqtt magic loop
	mqttclient.loop_start()

	# Create an instance of the IndiClient class and initialize its host/port members
	indiclient = IndiClient()
	indiclient.setServer(INDI_HOST,INDI_PORT)

	while True:
		# Connect to INDI server or loop forever until INDI server available
		while not indiclient.isServerConnected():
			if MQTT_POLLING > 0:
				# Set observatory status
				mqttclient.publish(MQTT_ROOT.lower() + "/status", "OFF")

			try:
				if not indiclient.connectServer():
					logger.debug("INDI server at " + indiclient.getHost() + ":" + str(indiclient.getPort()) + " not available. Retrying in 10 seconds")
					time.sleep(10)
			except KeyboardInterrupt:
				shutdown()
			except Exception as err:
				logger.error("Unexpected error connecting to INDI server", err)

		if indiclient.isServerConnected():
			# Must wait after INDI connection established
			time.sleep(1)

			if MQTT_POLLING > 0:
				# Set observatory status
				mqttclient.publish(MQTT_ROOT.lower() + "/status", "ON")

				try:
					# Get all devices
					devices = indiclient.getDevices()

					# Get properties and their associated values for all devices
					observatory_json = getJSON(devices)

					# Send MQTT message
					sendMQTT(observatory_json)

					# Loop every n seconds
					time.sleep(MQTT_POLLING)
				except KeyboardInterrupt:
					shutdown()
				except Exception as err:
					logger.error("Unexpected error timed polling INDI server", err)
			else:
				time.sleep(10)
