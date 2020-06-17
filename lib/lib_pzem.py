#!/usr/bin/env python3
#############################################################################
###################### Helper Library for PZEM ##############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import minimalmodbus # sudo pip3 install minimalmodbus
import time

class PZEM():

 VOLT = 0 # voltage - V
 AMP  = 1 # current - A
 WATT = 3 # power - W
 WHR  = 5 # energy - Wh
 FREQ = 7 # line frequency - Hz
 PWRF = 8 # power factor

 def __init__(self, port, slaveaddress, timeout=0.1):
  self.busy = False
  self.initialized = False
  self.port = port
  self.timeout = timeout
  self.address = slaveaddress
  self.connect()

 def connect(self):
  try:
   self.dev = minimalmodbus.Instrument(self.port,self.address,close_port_after_each_call=True)
   self.dev.serial.timeout = self.timeout
   self.dev.serial.baudrate = 9600
   self.initialized = True
   self.busy = True
   testval = self.readraw(0,self.VOLT,1)
   if testval == None or testval == False:
    time.sleep(0.5)
    testval = self.readraw(1,self.AMP,2)
   if testval == None or testval == False:
    self.initialized = False
    self.dev = None
   self.busy = False
  except Exception as e:
   print("PZEM Exception: ",str(e))
   self.initialized = False
   self.dev = None
   self.busy = False

 def readraw(self,readtype,val,vallen):
   res = None
   if self.timeout<1: # check if retry is needed
    cc = 1
   else:
    cc = 3
   while (res is None) and (cc>0):
    try:
     if readtype==0:
       res = self.dev.read_register(val,vallen,4)
     else:
       res = self.dev.read_registers(val,vallen,4)
    except Exception as e:
     if self.timeout>1:
      print("Slow PZEM error:",str(e))
    cc = cc-1
   return res

 def read_value(self, valuetype=0):
  res = None
  if self.initialized:
    if self.busy: # wait if line is occupied
      cc = 10
      while (self.busy) and (cc>0):
       time.sleep(0.3)
       cc = cc-1
    if self.busy==False:
     self.busy = True
     vallen = 2
     if valuetype in [self.VOLT, self.FREQ]:
      vallen = 1
     try:
      if valuetype in [self.VOLT, self.FREQ, self.PWRF]:
       res = self.readraw(0,int(valuetype),int(vallen))
      else:
       res = self.readraw(1,int(valuetype),int(vallen))
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

def request_pzem_device(sport,saddress,ttimeout=0.1):
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
  pzem_devices.append(PZEM(sport,saddress,ttimeout))
  return pzem_devices[-1]
