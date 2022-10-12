#!/usr/bin/env python3
#############################################################################
###################### Helper Library for HDHK ##############################
#############################################################################
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import minimalmodbus # sudo pip3 install minimalmodbus

class HDHK():

 def __init__(self, port, slaveaddress,ch=8):
  self.busy = False
  self.initialized = False
  self.port = port
  self.fw = 0
  self.prod = ""
  self.address = slaveaddress
  self.channels=ch
  if ch==8:
    self.startreg = 40
  else:
    self.startreg = 8
  self.connect()

 def connect(self):
  try:
   self.dev = minimalmodbus.Instrument(self.port,self.address,close_port_after_each_call=True)
   self.dev.mode = minimalmodbus.MODE_RTU
   self.dev.serial.timeout = 1
   self.dev.serial.baudrate = 9600
   self.dev.serial.bytesize = 8
   #self.dev.serial.parity = serial.PARITY_NONE
   self.dev.serial.stopbits = 1   
   self.initialized = True
   self.busy = False
   self.fw = self.dev.read_register(0,0,3) #version
   if self.fw == None or self.fw == False or self.fw == 0:
    self.initialized = False
    self.dev = None
   else:
    testval = self.dev.read_register(1,0,3) #first range
    testval2 = self.dev.read_register(2,0,3) #second range
    testval3 = hex(self.dev.read_register(4,0,3)) #date
    self.prod = "HD" + str(testval) + "A" + str(testval2) + "A (20"+ testval3[2:4] + "/" + testval3[4:6] + ") v"+ str(self.fw)
  except Exception as e:
   self.initialized = False
   self.dev = None

 def read_value(self, valuetype=0):
  res = None
  if self.initialized and self.busy==False:
   self.busy = True
   try:
     res = self.dev.read_register(self.startreg+int(valuetype),0,3,False)
   except Exception as e:
    pass
   if res is not None:
     res = round((res * 0.01),2)
   self.busy = False
  return res

hdhk_devices = []

def request_hdhk_device(sport,saddress,ch=8):
  for i in range(len(hdhk_devices)):
   if (hdhk_devices[i].port == str(sport)) and (int(hdhk_devices[i].address) == int(saddress)):
    return hdhk_devices[i]
  hdhk_devices.append(HDHK(sport,saddress,ch))
  return hdhk_devices[-1]
