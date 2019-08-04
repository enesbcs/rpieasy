#!/usr/bin/env python3
#############################################################################
################### Helper Library for BLE Mi Flora #########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# Based on:
#
#  https://github.com/kipe/miplant
#   MIT License
#   Copyright (c) 2016 Kimmo Huoman
#
from bluepy import btle
from datetime import datetime, timedelta
from struct import unpack

_HANDLE_WRITE_MODE_CHANGE = 0x33
_HANDLE_READ_SENSOR_DATA = 0x35
_HANDLE_READ_VERSION_BATTERY = 0x38
_DATA_MODE_CHANGE = bytes([0xA0, 0x1F])

class MiFlora():

    def __init__(self, address,cachetimeout=60): # timeout in seconds
     self.timeout = cachetimeout
     if self.timeout<5:
      self.timeout=5
     self.address = address
     self.busy = False
     self.battery = 0
     self._firmware_version = ""
     self._fw_last_read = (datetime.now() - timedelta(hours=24))
     self._temperature = None
     self._light = None
     self._moisture = None
     self._conductivity = None
     self._last_read = self._fw_last_read

    def battery_level(self):
        self.firmware_version()
        return self.battery

    def firmware_version(self):
        if (self._firmware_version=="") or (datetime.now() - timedelta(hours=1) > self._fw_last_read) and (self.busy==False): # 1 hour timeout fixed
          self._fw_last_read = datetime.now()
          try:
            self.busy = True
            peripheral = btle.Peripheral(self.address)
            received_bytes = bytearray(peripheral.readCharacteristic(_HANDLE_READ_VERSION_BATTERY))
            self.battery = received_bytes[0]
            self._firmware_version = "".join(map(chr, received_bytes[2:]))
            peripheral.disconnect()
            self.busy = False
          except:
            self.busy = False
            self.battery = 0
            self._firmware_version = ""
        return self._firmware_version

    def read(self):
       if (datetime.now() - timedelta(seconds=self.timeout) > self._last_read) and (self.busy==False):
        self._last_read = datetime.now()
        try:
            self.busy = True
            peripheral = btle.Peripheral(self.address)
            peripheral.writeCharacteristic(_HANDLE_WRITE_MODE_CHANGE, _DATA_MODE_CHANGE, withResponse=True)

            received_bytes = bytearray(peripheral.readCharacteristic(_HANDLE_READ_SENSOR_DATA))
#            print("ble read ",received_bytes) # DEBUG!
            self._temperature, self._light, self._moisture, self._conductivity = unpack('<hxIBhxxxxxx', received_bytes)
            self._temperature = float(self._temperature) / 10.0
            peripheral.disconnect()
            self.busy = False
            return True
        except Exception as e:
            print(e)
            self.busy = False
            return False

    def get_temperature(self):
        self.read()
        return self._temperature

    def get_light(self):
        self.read()
        return self._light

    def get_moisture(self):
        self.read()
        return self._moisture

    def get_conductivity(self):
        self.read()
        return self._conductivity

flora_devices = []

def request_flora_device(address,timeout=60):
 for i in range(len(flora_devices)):
  if (str(flora_devices[i].address).lower().strip() == str(address).lower().strip()):
   return flora_devices[i]
 flora_devices.append(MiFlora(address,timeout))
 return flora_devices[-1]
