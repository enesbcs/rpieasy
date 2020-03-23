#!/usr/bin/env python3
#############################################################################
################### Helper Library for ADS1x15 ADC ##########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import misc
import rpieGlobals
import time
import Adafruit_ADS1x15 as ADS

class ADSEntity():

 def __init__(self, i2cAddress, busnum=1, atype=0):
  self.busy = False
  self.initialized = False
  self.i2cAddress = int(i2cAddress)
  self.busnum = int(busnum)
  self.values = [0,0,0,0]
  try:
   if atype==10 or atype==0:
       self.adc = ADS.ADS1015(address=self.i2cAddress,busnum=self.busnum)
       self.initialized = True
   else:
       self.adc = ADS.ADS1115(address=self.i2cAddress,busnum=self.busnum)
       self.initialized = True
  except:
   self.initialized = False

 def ADread(self,channel,again=None):
  val = self.values[channel]
  try:
   if self.busy:
    time.sleep(0.1)
   if (self.busy==False):
    self.busy=True
    val = self.adc.read_adc(channel,gain=again)
    self.busy=False
    self.values[channel]=val
  except:
    self.busy=False
    val = 0
  return val

ads_devices = []

def request_ads_device(i2caddress,busnum,atype):
  global ads_devices
  for i in range(len(ads_devices)):
   if (ads_devices[i].i2cAddress == int(i2caddress)):
    return ads_devices[i]
  ads_devices.append(ADSEntity(i2caddress,busnum,atype))
  return ads_devices[-1]
