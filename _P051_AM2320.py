#!/usr/bin/env python3
#############################################################################
######################## AM2320 plugin for RPIEasy ##########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import smbus
import time

def _combine_bytes(msb, lsb):
 return msb << 8 | lsb

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 51
 PLUGIN_NAME = "Environment - AM2320"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Humidity"
 ADDR=0x5c

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
  self.readinprogress = 0
  self.valuecount = 2
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.samples = 3
  self.preread = self.samples*2000 # 3 * 2 sec
  self.TARR = []
  self.HARR = []
  self.i2cbus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.TARR = []
  self.HARR = []
  self.uservar[0] = 0
  self.uservar[1] = 0
  if self.enabled:
   try:
    try:
     i2cl = self.i2c
    except:
     i2cl = -1
    self.i2cbus = gpios.HWPorts.i2c_init(i2cl)
    if i2cl==-1:
     self.i2cbus = gpios.HWPorts.i2cbus
    if self.i2cbus is not None:
     if self.interval>2:
      nextr = self.interval-2
     else:
      nextr = self.interval
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
     self.lastread = 0
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!")
     self.initialized = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.initialized = False
    self.i2cbus = None

 def webform_load(self): # create html page for settings
  webserver.addFormNote("I2C address is fixed 0x5c! You can check it at <a href='i2cscanner'>i2cscan</a> page.")
  webserver.addFormCheckBox("Oversampling","plugin_051_over",self.timer2s)
  webserver.addFormNote("It is not strictly necessary as AM2320 gives stable output values!")
  return True

 def webform_save(self,params): # process settings post reply
  if (webserver.arg("plugin_051_over",params)=="on"):
   self.timer2s = True
  else:
   self.timer2s = False
  return True

 def timer_two_second(self):
  if self.timer2s and self.initialized and self.readinprogress==0 and self.enabled:
   if self._nextdataservetime-rpieTime.millis()<=self.preread:
    self.readinprogress = 1
    self.p051_get_value()
    self.readinprogress = 0
  return self.timer2s

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0:
   prevt = self.uservar[0]
   prevh = self.uservar[1]
   self.readinprogress = 1
   self.p051_get_value()
   if len(self.TARR)==1:
     self.set_value(1,self.TARR[0],False)
   if len(self.HARR)==1:
     self.set_value(2,self.HARR[0],False)
   if len(self.TARR)>1:
    atemp = round((sum(self.TARR) / len(self.TARR)),3)
    if ((max(self.TARR) - min(self.TARR)) > 2): # too much deviation found for temp
       difft = abs(max(self.TARR) - atemp)
       if (difft > abs(atemp-min(self.TARR))):
        difft = abs(atemp-min(self.TARR))
       if (difft < 1):
        difft = 1
       if (difft > 5):
        difft = 5
       TARR2 = []
       for i in range(0,len(self.TARR)):
        if (abs(atemp-self.TARR[i]) <= difft):
         TARR2.append(self.TARR[i])
       if len(TARR2)>0:
        atemp = round((sum(TARR2) / len(TARR2)),3)
    self.set_value(1,atemp,False)
   if len(self.HARR)>1:
    ahum = round((sum(self.HARR) / len(self.HARR)),2)
    if ((max(self.HARR) - min(self.HARR)) > 4): # too much deviation for humidity
       diffh = abs(max(self.HARR) - ahum)
       if (diffh > abs(ahum-min(self.HARR))):
        diffh = abs(ahum-min(self.HARR))
       if (diffh < 2):
        diffh = 2
       if (diffh > 8):
        diffh = 8
       HARR2 = []
       for i in range(0,len(self.HARR)):
        if (abs(ahum-self.HARR[i]) <= diffh):
         HARR2.append(self.HARR[i])
       if len(HARR2)>0:
        ahum = round((sum(HARR2) / len(HARR2)),2)
    self.set_value(2,ahum,False)
   if len(self.TARR)<1 or len(self.HARR)<1: # no value returned, cheating
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"AM2320 read failed, using cached value!")
    self.set_value(1,prevt,False)
    self.set_value(2,prevh,False)
   if float(self.uservar[0])!=0 and float(self.uservar[1])!=0:
    self.plugin_senddata()
#   print(self.TARR,self.HARR) # DEBUG only!
   self.TARR = []
   self.HARR = []
   self._lastdataservetime = rpieTime.millis()
   self._nextdataservetime = self._lastdataservetime + (self.interval*1000)
   result = True
   self.readinprogress = 0
  return result

 def readam2320(self):
  try:
   bus = self.i2cbus
  except:
   self.i2cbus = None
   return 0,0
  temp = None
  humi = None
  try:
   bus.write_quick(self.ADDR)
  except:
   pass
  time.sleep(0.001)
  try:
   bus.write_word_data(self.ADDR,0x03,0x0400)
  except:
   return (temp, humi)
  time.sleep(0.0016)
  data = bus.read_i2c_block_data(self.ADDR,0x03)
  if data[0] != 0x03 or data[1] != 0x04:
   return (temp, humi)
  if len(data)>7:
   temp = _combine_bytes(data[4], data[5])
   if temp & 0x8000:
    temp = -(temp & 0x7FFF)
   temp /= 10.0
   humi = _combine_bytes(data[2], data[3]) / 10.0
  return (temp, humi)

 def p051_get_value(self):
   if rpieTime.millis()>=(self.lastread+2000):
    humidity = None
    temperature = None
    try:
     temperature, humidity = self.readam2320()
    except:
     humidity = None
     temperature = None
    if humidity is not None and temperature is not None:
     self.HARR.append(round(humidity, 2))
     self.TARR.append(round(temperature, 3))
    self.lastread = rpieTime.millis()
