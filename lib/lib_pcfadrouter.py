#!/usr/bin/env python3
#############################################################################
################# Helper Library for PCF8591 ADC/DAC ########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import gpios
import misc
import rpieGlobals
import time

class PCFADEntity():

 def __init__(self, i2cAddress):
  self.busy = False
  self.lastread = 0
  self.initialized = False
  self.i2cAddress = int(i2cAddress)
  self.bus = None
  self.daenabled = 0
  self.values = [0,0,0,0]
  try:
   i2cok = gpios.HWPorts.i2c_init()
   if i2cok:
    self.bus = gpios.HWPorts.i2cbus
    self.initialized = True
  except Expception as e:
   self.bus = None
   print(e)

 def DAenable(self):
  self.daenabled = 0x40

 def DAdisable(self):
  self.daenabled = 0

 def DAwrite(self,value):
  self.DAenable()
  if self.busy:
   time.sleep(0.1)
  if self.busy==False:
   try:
    self.bus.write_byte_data(self.i2cAddress,self.daenabled,(int(value) & 0xFF))
   except Exception as e:
    print(e)

 def ADread(self,channel):
  try:
   val = self.values[channel]
   if self.busy:
    time.sleep(0.1)
   if (self.busy==False):
    self.busy=True
    self.bus.write_byte(self.i2cAddress,channel | self.daenabled)
    self.bus.read_byte(self.i2cAddress) # read previous value
    val = self.bus.read_byte(self.i2cAddress) # read fresh value
    self.busy=False
    self.values[channel]=val
  except Exception as e:
   print(e)
   val = 0
  return val

pcfad_devices = []

def request_pcfad_device(mportnum):
 i2caddress, realpin = get_pcfad_pin_address(mportnum)
 if realpin > -1:
  for i in range(len(pcfad_devices)):
   if (pcfad_devices[i].i2cAddress == int(i2caddress)):
    return pcfad_devices[i]
  pcfad_devices.append(PCFADEntity(i2caddress))
  return pcfad_devices[-1]
 else:
  return None

def request_pcfad_device_byaddr(i2caddress):
  for i in range(len(pcfad_devices)):
   if (pcfad_devices[i].i2cAddress == int(i2caddress)):
    return pcfad_devices[i]
  pcfad_devices.append(PCFADEntity(i2caddress))
  return pcfad_devices[-1]

def get_pcfad_pin_address(pinnumber):
 number = int(pinnumber)
 ia=0
 pn=-1
 if number>0 and number<33:
  ia, pn = divmod(number,4)
  if pn==0:
   ia-=1
   pn=3
  else:
   pn-=1
  ia+=0x48
 return ia, pn

