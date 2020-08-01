#!/usr/bin/env python3
#############################################################################
################### Helper Library for MCP3008 ADC ##########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import misc
import rpieGlobals
import time
import spidev

class ADCEntity():

 def __init__(self, busnum=0, devnum=0):
  self.busy = False
  self.initialized = False
  self.busnum = int(busnum)
  self.devnum = int(devnum)
  self.values = [0,0,0,0,0,0,0,0,0]
  try:
   self.spi = spidev.SpiDev()
   self.spi.open(self.busnum,self.devnum)
   self.spi.max_speed_hz=1000000
   self.initialized = True
  except:
   self.initialized = False
   self.devnum = -1
   self.busnum = -1
   self.spi = None

 def ADread(self,channel):
  channel = int(channel)
  if channel > 7 or channel < 0:
   return -1
  val = self.values[channel]
  try:
   if self.busy:
    time.sleep(0.1)
   if (self.busy==False):
    self.busy=True
    rawData = self.spi.xfer2([1, 8 + channel << 4, 0])
    val = ((rawData[1] & 3) << 8) + rawData[2]
    self.busy=False
    self.values[channel]=val
  except Exception as e:
    self.busy=False
    val = 0
  return val

adc_devices = []

def request_adc_device(busnum=0,devnum=0):
  global adc_devices
  for i in range(len(adc_devices)):
   if (adc_devices[i].devnum == int(devnum)) and (adc_devices[i].busnum == int(busnum)):
    return adc_devices[i]
  adc_devices.append(ADCEntity(busnum,devnum))
  return adc_devices[-1]
