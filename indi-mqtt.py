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
import paho.mqtt.publish as publish
import signal
import json
import argparse

__author__ = 'Radek Kaczorek'
__copyright__ = 'Copyright 2019, Radek Kaczorek'
__license__ = 'GPL-3'
__version__ = '1.0.0'

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# Default options
VERBOSE = False
DEBUG = False
LIST_TOPICS = False
CONFIG_FILE = "/etc/indi-mqtt.conf"

# INDI
INDI_HOST = 'localhost'
INDI_PORT = 7624
INDI_RECONNECT = 30

# MQTT
MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_ROOT = 'OBSERVATORY'
MQTT_POLLING = 10
MQTT_JSON = False

parser = argparse.ArgumentParser()
parser.add_argument("-c ", "--config", help="configuration file path (default = /etc/indi-mqtt.conf)")
parser.add_argument("-v", "--verbose", help="enable verbose output", action="store_true")
parser.add_argument("-d", "--debug", help="enable debugging", action="store_true")
parser.add_argument("-l", "--list_topics", help="list available MQTT topics", action="store_true")
parser.add_argument("-j", "--mqtt_json", help="enable full json on MQTT root/json", action="store_true")
parser.add_argument("--indi_host", help="INDI server hostname or IP (default = localhost)")
parser.add_argument("--indi_port", help="INDI server port number (default = 7624)")
parser.add_argument("--indi_reconnect", help="INDI server reconnect time in seconds (default = 10)")
parser.add_argument("--mqtt_host", help="MQTT server hostname or IP (default = localhost)")
parser.add_argument("--mqtt_port", help="MQTT server port number (default = 1883)")
parser.add_argument("--mqtt_root", help="MQTT root topic name (default = OBSERVATORY)")
parser.add_argument("--mqtt_polling", help="MQTT polling time in seconds (default = 10)")
args = parser.parse_args()

if args.config:
	CONFIG_FILE = args.config
if args.verbose:
	VERBOSE = True
if args.debug:
	DEBUG = True
if args.list_topics:
	LIST_TOPICS = True

if os.path.isfile(CONFIG_FILE):
		if VERBOSE:
			print("Using configuration from " + CONFIG_FILE)
		config = configparser.ConfigParser()
		config.read(CONFIG_FILE)
		if 'INDI_HOST' in config['INDI']:
			INDI_HOST = config['INDI']['INDI_HOST']
		if 'INDI_PORT' in config['INDI']:
			INDI_PORT = int(config['INDI']['INDI_PORT'])
		if 'INDI_RECONNECT' in config['INDI']:
			INDI_RECONNECT = int(config['INDI']['INDI_RECONNECT'])
		if 'MQTT_HOST' in config['MQTT']:
			MQTT_HOST = config['MQTT']['MQTT_HOST']
		if 'MQTT_PORT' in config['MQTT']:
			MQTT_PORT = int(config['MQTT']['MQTT_PORT'])
		if 'MQTT_ROOT' in config['MQTT']:
			MQTT_ROOT = config['MQTT']['MQTT_ROOT']
		if 'MQTT_POLLING' in config['MQTT']:
			MQTT_POLLING = int(config['MQTT']['MQTT_POLLING'])
		if 'MQTT_JSON' in config['MQTT']:
			if config['MQTT']['MQTT_JSON'].lower() == 'true':
				MQTT_JSON = True

if args.indi_host:
	INDI_HOST = args.indi_host
if args.indi_port:
	INDI_PORT = int(args.indi_port)
if args.indi_reconnect:
	INDI_RECONNECT = int(args.indi_reconnect)
if args.mqtt_host:
	MQTT_HOST = args.mqtt_host
if args.mqtt_port:
	MQTT_PORT = int(args.mqtt_port)
if args.mqtt_root:
	MQTT_ROOT = args.mqtt_root
if args.mqtt_polling:
	MQTT_POLLING = int(args.mqtt_polling)
if args.mqtt_json:
	MQTT_JSON = True

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

def shutdown():
	print('Exiting\nGood Bye.\n')
	sys.exit()

def term_handler(signum, frame):
        raise KeyboardInterrupt

# The IndiClient class which inherits from the module PyIndi.BaseClient class
# It should implement all the new* pure virtual functions.
class IndiClient(PyIndi.BaseClient):
	def __init__(self):
		super(IndiClient, self).__init__()
		self.logger = logging.getLogger('__name__')
		self.isConnected = False
		if VERBOSE:
			self.logger.info('Creating an instance of INDI client')
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
		self.isConnected = True
		if VERBOSE:
			self.logger.info("INDI server connected to " + self.getHost() + ":" + str(self.getPort()))
	def serverDisconnected(self, code):
		self.isConnected = False
		if VERBOSE:
			self.logger.info("INDI server disconnected from " + str(self.getHost()) + ":" + str(self.getPort()))

def getJSON(devices):
	# Construct json {device:{property:value, property, value}, device:{property:value, property, value}}
	observatory_json = json.loads("{}")
	for device in devices:
		device_properties_json = json.loads("{}")
		device_type = strDeviceType(device.getDriverInterface())
		properties = device.getProperties()
		for property in properties:
			device_property_json = json.loads("{}")
			property_name = property.getName()
			if property.getType() == PyIndi.INDI_TEXT:
				tpy = property.getText()
				for t in tpy:
					device_property_json.update({t.name:t.text})
					device_properties_json.update({property_name:device_property_json})
					observatory_json.update({device_type:device_properties_json})
			elif property.getType()==PyIndi.INDI_NUMBER:
				tpy = property.getNumber()
				for t in tpy:
					device_property_json.update({t.name:t.value})
					device_properties_json.update({property_name:device_property_json})
					observatory_json.update({device_type:device_properties_json})
			elif property.getType()==PyIndi.INDI_SWITCH:
				tpy = property.getSwitch()
				for t in tpy:
					device_property_json.update({t.name:strISState(t.s)})
					device_properties_json.update({property_name:device_property_json})
					observatory_json.update({device_type:device_properties_json})
			elif property.getType()==PyIndi.INDI_LIGHT:
				tpy = property.getLight()
				for t in tpy:
					device_property_json.update({t.name:strIPState(t.s)})
					device_properties_json.update({property_name:device_property_json})
					observatory_json.update({device_type:device_properties_json})
			elif property.getType()==PyIndi.INDI_BLOB:
				tpy = property.getBLOB()
				for t in tpy:
					device_property_json.update({t.name:'<blob ' + str(t.size) + ' bytes>'})
					device_properties_json.update({property_name:device_property_json})
					observatory_json.update({device_type:device_properties_json})

	return observatory_json

def sendMQTT(observatory_json):
	if DEBUG:
		print(json.dumps(observatory_json, indent=4, sort_keys=False))
	try:
		# Publish entire json
		if MQTT_JSON:
			publish.single(MQTT_ROOT.lower() + "/json", json.dumps(observatory_json), hostname=MQTT_HOST, port=MQTT_PORT)

		# Publish properties and values
		for device in observatory_json:
			for property in observatory_json[device]:
				for key in observatory_json[device][property]:
					topic = MQTT_ROOT + '/' + device + '/' + property + '/' + key
					payload = observatory_json[device][property][key]
					if LIST_TOPICS:
						print(topic.lower())
					if DEBUG:
						print(topic.lower(), payload, sep=" = ")
					publish.single(topic.lower(), payload, hostname=MQTT_HOST, port=MQTT_PORT)
		if VERBOSE:
			indiclient.logger.info("Publish MQTT message to " + MQTT_HOST + ":" + str(MQTT_PORT))

	except:
		if VERBOSE:
			indiclient.logger.info("MQTT server not available on " + MQTT_HOST + ":" + str(MQTT_PORT))

# register term handler
signal.signal(signal.SIGTERM, term_handler)

if __name__ == '__main__':
	# Create an instance of the IndiClient class and initialize its host/port members
	indiclient = IndiClient()
	indiclient.setServer(INDI_HOST,INDI_PORT)

	while True:
		try:
			# Connect to INDI server or loop forever until INDI server available
			while not indiclient.connectServer():
				try:
					if VERBOSE:
						indiclient.logger.info("INDI server not available on " + indiclient.getHost() + ":" + str(indiclient.getPort()) + ". Retrying in " + str(INDI_RECONNECT) + " seconds")
					time.sleep(INDI_RECONNECT)
				except KeyboardInterrupt:
					shutdown()

			# Wait 1s after connection
			time.sleep(1)

			while indiclient.isConnected:
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
		except KeyboardInterrupt:
			shutdown()
