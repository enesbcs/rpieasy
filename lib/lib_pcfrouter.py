#!/usr/bin/env python3
#############################################################################
#################### Helper Library for PCF8574 #############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import gpios
import misc
import rpieGlobals
import time

class PCFEntity():

 def __init__(self, i2cAddress):
  self.externalintsetted = False
  self.extinta = 0
  self.busy = False
  self.lastread = 0
  self.initialized = False
  self.i2cAddress = int(i2cAddress)
  self.bus = None
  self.lastportvalue = None
  self.callbacks = [None,None,None,None,None,None,None,None]
  try:
   i2cok = gpios.HWPorts.i2c_init()
   if i2cok:
    self.bus = gpios.HWPorts.i2cbus
    self.initialized = True
  except:
   self.bus = None

 def getallpinvalues(self,Force=False):
  val = self.lastportvalue
  if (Force) or (self.busy==False):
   self.busy = True
   if (Force) or (time.time()-self.lastread)>=(1/50):
    try:
     prevval = self.lastportvalue
     val = self.bus.read_byte(self.i2cAddress)
     self.lastportvalue = val
     self.lastread = time.time()
     if prevval is not None and prevval!=val and self.initialized:
      for b in range(8):
       if self.callbacks[b] is not None:
        if isbitset(prevval,b)!=isbitset(val,b):
         self.callbacks[b](b,int(isbitset(val,b)))
    except:
     val = None
   self.busy = False
  return val

 def readpin(self,pinnum): # 0-7
  self.getallpinvalues()
  return isbitset(self.lastportvalue,pinnum)

 def writepin(self,pinnum,value): # pinnum 0-7, value 0-1
  result = False
  if (self.busy==False):
   self.busy = True
   try:
    val = self.bus.read_byte(self.i2cAddress)
    if isbitset(val,pinnum):
     bv = 1
    else:
     bv = 0
    if bv!=value:
     if value==0:
      val-= (1 << pinnum)
     else:
      val+= (1 << pinnum)
     self.bus.write_byte(self.i2cAddress,val)
    if self.lastportvalue is not None and self.lastportvalue!=val and self.initialized:
      for b in range(8):
       if self.callbacks[b] is not None:
        if isbitset(self.lastportvalue,b)!=isbitset(val,b):
         self.callbacks[b](b,int(isbitset(val,b)))
   except Exception as e:
    print(e)
   self.busy = False

 def writepinlist(self,pinnums,value): # pinnum array 0-7, value 0-1
  result = False
  if (self.busy==False):
   self.busy = True
   try:
    val = self.bus.read_byte(self.i2cAddress)
    prevval = val
    for pinnum in pinnums:
     if isbitset(val,pinnum):
      bv = 1
     else:
      bv = 0
     if bv!=value:
      if value==0:
       val-= (1 << pinnum)
      else:
       val+= (1 << pinnum)
    if val!=prevval:
     self.bus.write_byte(self.i2cAddress,val)
    if self.lastportvalue is not None and self.lastportvalue!=val and self.initialized:
      for b in range(8):
       if self.callbacks[b] is not None:
        if isbitset(self.lastportvalue,b)!=isbitset(val,b):
         self.callbacks[b](b,int(isbitset(val,b)))
   except Exception as e:
    print(e)
   self.busy = False

 def interruptcalled(self,channel):
  if self.initialized:
   self.getallpinvalues(True)

 def setexternalint(self,intpin):
#   if int(intpin)>-1 and int(intpin)!=self.extinta:
   if int(intpin)>-1:
    if self.extinta>-1:
     try:
      gpios.HWPorts.remove_event_detect(self.extinta)
     except:
      pass
    try:
      self.extinta = int(intpin)
      gpios.HWPorts.add_event_detect(self.extinta,gpios.FALLING,self.interruptcalled) # needs INPUT-PULLUP!
      self.externalintsetted = True
    except Exception as e:
      self.externalintsetted = False
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Adding PCF interrupt failed "+str(e))

 def setcallback(self,pinnum,callback): # pinnum 0-7
   if pinnum>=0 and pinnum<8:
    self.callbacks[pinnum] = callback

 def __del__(self):
    self.initialized = False
    # remove event handler
    if self.extinta>0:
     try:
      gpios.HWPorts.remove_event_detect(self.extinta)
     except:
      pass

pcf_devices = []

def isbitset(value,bitnum):
 if value & (1 << bitnum):
   return True
 else:
   return False

def request_pcf_device(mportnum):
 i2caddress, realpin = get_pcf_pin_address(mportnum)
 if realpin > -1:
  for i in range(len(pcf_devices)):
   if (pcf_devices[i].i2cAddress == int(i2caddress)):
    return pcf_devices[i]
  pcf_devices.append(PCFEntity(i2caddress))
  return pcf_devices[-1]
 else:
  return None

def get_pcf_pin_address(pinnumber):
 number = int(pinnumber)
 ia=0
 pn=-1
 if number>0 and number<129:
  ia, pn = divmod(number,8)
  if pn==0:
   ia-=1
   pn=7
  else:
   pn-=1
  ia+=0x20
  if ia>0x27 and ia<=0x2F:
   ia += 0x10 # PCF8574A
 return ia, pn
 