#!/usr/bin/env python3
#############################################################################
###################### Helper Library for PZEM ##############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import minimalmodbus # sudo pip3 install minimalmodbus
import time
import rpieGlobals
import misc

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
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PZEM exception: "+str(e))
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
  res = False
  try:
   self.dev._perform_command(66, b'')
   res = True
  except Exception as e:
   res = False
  if res==False:
   try:
    self.dev._performCommand(66,'')
    res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PZEM016 reset error: "+str(e))
    res = False
  return res

class PZEM4():

 VOLT = 0 # voltage - V
 AMP  = 1 # current - A
 WATT = 3 # power - W
 WHR  = 5 # energy - Wh
 FREQ = 7 # line frequency - Hz
 PWRF = 8 # power factor

 def __init__(self, port, slaveaddress, timeout=3):
  self.busy = False
  self.initialized = False
  self.port = port
  self.timeout = timeout
  self.address = slaveaddress
  self._volt = None
  self._amp  = None
  self._watt = None
  self._whr  = None
  self._freq = None
  self._pwrf = None
  self.lastread = 0
  self.readinprogress = False
  self.errorcount = 0
  self.connect(True)

 def connect(self,testit=True):
  try:
   self.busy = True
   self.dev = minimalmodbus.Instrument(self.port,self.address,close_port_after_each_call=True)
   self.dev.serial.timeout = self.timeout
   self.dev.serial.baudrate = 9600
   self.busy = False
   self.initialized = True
   if testit:
    testval = self.readraw()
    if testval is None or testval == False or self._volt is None:
     time.sleep(0.5)
     testval = self.readraw()
    if testval is None or testval == False or self._volt is None:
     self.initialized = False
     self.dev = None
   self.errorcount = 0
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PZEM exception: "+str(e))
   if testit:
    self.initialized = False
    self.dev = None
    self.busy = False

 def readraw(self):
  data = None
  if time.time()-self.lastread>2:
   if self.readinprogress == False and self.busy==False:
    self.readinprogress = True
    try:
     data = self.dev.read_registers(0,10,4)
     self.lastread = time.time()
    except Exception as e:
     data = None
     self.errorcount += 1
#    print(data)#debug
    try:
     if data is not None:
      if len(data)>9:
       self._volt  = data[0] / 10.0 # [V]
       self._amp  = (data[1] + (data[2] << 16)) / 1000.0 # [A]
       self._watt = (data[3] + (data[4] << 16)) / 10.0 # [W]
       self._whr  = data[5] + (data[6] << 16) # [Wh]
       self._freq = data[7] / 10.0 # [Hz]
       self._pwrf = data[8] / 100.0
    except Exception as e:
     pass
    self.readinprogress = False
    if self.errorcount>3:
     self.connect(False)
  return data

 def read_value(self, valuetype=0):
  res = None
  if self.initialized:
    self.readraw()
    if valuetype == self.VOLT:
     return self._volt
    elif valuetype == self.AMP:
     return self._amp
    elif valuetype == self.WATT:
     return self._watt
    elif valuetype == self.WHR:
     return self._whr
    elif valuetype == self.FREQ:
     return self._freq
    elif valuetype == self.PWRF:
     return self._pwrf
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
  res = False
  try:
   self.dev._perform_command(66, b'')
   res = True
  except Exception as e:
   res = False
  if res==False:
   try:
    self.dev._performCommand(66,'')
    res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PZEM016 reset error: "+str(e))
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

def request_pzem4_device(sport,saddress,ttimeout=3):
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
  pzem_devices.append(PZEM4(sport,saddress,ttimeout))
  return pzem_devices[-1]
