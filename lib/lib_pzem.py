#!/usr/bin/env python3
#############################################################################
###################### Helper Library for PZEM ##############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import minimalmodbus # sudo pip3 install minimalmodbus

class PZEM():

 VOLT = 0 # voltage - V
 AMP  = 1 # current - A
 WATT = 3 # power - W
 WHR  = 5 # energy - Wh
 FREQ = 7 # line frequency - Hz
 PWRF = 8 # power factor

 def __init__(self, port, slaveaddress):
  self.busy = False
  self.initialized = False
  self.port = port
  self.address = slaveaddress
  self.connect()

 def connect(self):
  try:
   self.dev = minimalmodbus.Instrument(self.port,self.address,close_port_after_each_call=True)
   self.dev.serial.timeout = 0.1
   self.dev.serial.baudrate = 9600
   self.initialized = True
   self.busy = False
   testval = self.dev.read_register(self.VOLT,1,4)
   if testval == None or testval == False:
    self.initialized = False
    self.dev = None
  except Exception as e:
   print("PZEM Exception: ",str(e))
   self.initialized = False
   self.dev = None

 def read_value(self, valuetype=0):
  res = None
  if self.initialized and self.busy==False:
   self.busy = True
   vallen = 2
   if valuetype in [self.VOLT, self.FREQ]:
    vallen = 1
   try:
    if valuetype in [self.VOLT, self.FREQ, self.PWRF]:
     res = self.dev.read_register(int(valuetype),int(vallen),4)
    else:
     res = self.dev.read_registers(int(valuetype),int(vallen),4)
     res = res[0]+(res[1]*65536)
   except Exception as e:
    pass
   if res is not None:
    if valuetype==self.AMP:
     res = round((res * 0.001),3)
    elif valuetype==self.WATT:
     res = round((res * 0.1),1)
   self.busy = False
  return res

 def changeAddress(self,newaddress):
  if newaddress == 0 or newaddress > 247:
   return False
  res = False
  try:
   self.dev.write_register(2, newaddress, 0, 6)
   res = True
  except:
   res = False
  if res:
   self.address = newaddress
   self.connect()
  return res

 def resetenergy(self):
  try:
   self.dev._performCommand(66,'')
   res = True
  except:
   res = False
  return res

pzem_devices = []

def request_pzem_device(sport,saddress):
  global pzem_devices
  sport = str(sport)
  try:
   saddress = int(saddress)
  except:
   saddress = 1
  for i in range(len(pzem_devices)):
   try:
    if (str(pzem_devices[i].port) == sport) and (int(pzem_devices[i].address) == saddress):
     return pzem_devices[i]
   except:
    pass
  pzem_devices.append(PZEM(sport,saddress))
  return pzem_devices[-1]
