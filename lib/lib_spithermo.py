#!/usr/bin/env python3
#############################################################################
############### Helper Library for SPI Thermocouple chips ###################
#############################################################################
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import misc
import rpieGlobals
import time
import spidev

class ThermoEntity():

 def __init__(self, busnum=0, devnum=0, dtype=6675):
  self.busy = False
  self.initialized = False
  self.busnum = int(busnum)
  self.devnum = int(devnum)
  self.values = 0
  try:
   self.spi = spidev.SpiDev()
   self.spi.open(self.busnum,self.devnum)
   self.spi.max_speed_hz=3900000
   self.initialized = True
  except Exception as e:
   self.initialized = False
   self.devnum = -1
   self.busnum = -1
   self.spi = None
  if dtype==6675:
   self.read = self.read6675
  elif dtype == 31855:
   self.read = self.read31855
  else:
   self.read = self.readDummy
   self.initialized = False

 def readDummy(self):
   return None

 def read6675(self): #max6675
  val = self.values
  try:
   if self.busy:
    time.sleep(0.1)
   if (self.busy==False):
    self.busy=True
    rawData = self.spi.readbytes(2)
    val = ((rawData[0] << 8 | rawData[1]) >> 3) * 0.25
    self.busy=False
    self.values=val
  except Exception as e:
    self.busy=False
    val = -1
  return val

 def read31855(self): #max31855
  val = self.values
  try:
   if self.busy:
    time.sleep(0.1)
   if (self.busy==False):
    self.busy=True
    rawData = self.spi.readbytes(4)
    val = rawData[0] << 8 | RawData[1]
    if val & 0x0001:
        return None
    val >>= 2
    if val & 0x2000:
        val -= 16384
    self.busy=False
    self.values=val
  except Exception as e:
    self.busy=False
    val = -1
  return val

thermo_devices = []

def request_thermo_device(busnum=0,devnum=0,dtype=6675):
  global thermo_devices
  for i in range(len(thermo_devices)):
   if (thermo_devices[i].devnum == int(devnum)) and (thermo_devices[i].busnum == int(busnum)):
    return thermo_devices[i]
  thermo_devices.append(ThermoEntity(busnum,devnum,dtype))
  return thermo_devices[-1]
