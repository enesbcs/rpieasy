#!/usr/bin/env python3
#############################################################################
###################### Helper Library for BME680 ############################
#############################################################################
#
# Copyright (C) 2023 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import smbus
import bme680

class BME680Dev():

 def __init__(self, i2cAddress, busnum=1):
  self.busy = False
  self.initialized = False
  self.i2cAddress = int(i2cAddress)
  self.busnum = int(busnum)
  self.i2c_bus = smbus.SMBus(self.busnum)
  self.dev = None
  self.lastval = {
      "temperature": 0,
      "pressure": 0,
      "humidity": 0,
      "gas": 0
  }

  try:
      self.dev = bme680.BME680(self.i2cAddress,self.i2c_bus)
      self.dev.set_humidity_oversample(bme680.OS_2X)
      self.dev.set_pressure_oversample(bme680.OS_4X)
      self.dev.set_temperature_oversample(bme680.OS_8X)
      self.dev.set_filter(bme680.FILTER_SIZE_3)
      self.dev.set_gas_status(bme680.ENABLE_GAS_MEAS)
      self.dev.set_gas_heater_temperature(320)
      self.dev.set_gas_heater_duration(150)
      self.dev.select_gas_heater_profile(0)
      self.initialized = True
  except Exception as e:
   print(e) #debug
   self.initialized = False

 def read_raw(self):
   if self.dev is not None and self.initialized:
    try:
     self.dev.get_sensor_data()
     self.lastval["temperature"] = self.dev.data.temperature
     self.lastval["pressure"] = self.dev.data.pressure
     self.lastval["humidity"] = self.dev.data.humidity
     if self.dev.data.heat_stable:
      self.lastval["gas"] = self.dev.data.gas_resistance
    except:
     pass
    return self.lastval

 def read(self): 
  try:
   if (self.busy==False):
    self.busy=True
    self.read_raw()
    self.busy=False
  except Exception as e:
    self.busy=False
  return self.lastval

bme_devices = []

def request_bme_device(busnum,i2caddress):
  for i in range(len(bme_devices)):
   if (bme_devices[i].i2cAddress == int(i2caddress) and bme_devices[i].busnum==int(busnum)):
    return bme_devices[i]
  bme_devices.append(BME680Dev(i2cAddress=i2caddress,busnum=busnum))
  return bme_devices[-1]
