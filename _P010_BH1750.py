#!/usr/bin/env python3
#############################################################################
##################### BH1750 plugin for RPIEasy #############################
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

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 10
 PLUGIN_NAME = "Environment - BH1750 Lux sensor"
 PLUGIN_VALUENAME1 = "Lux"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.samples = 3
  self.preread = self.samples*2000 # 3 * 2 sec
  self.LARR = []
  self.i2cbus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.LARR = []
  self.uservar[0] = 0
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
     self.enabled = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.enabled = False
    self.i2cbus = None

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x23","0x5c"]
  optionvalues = [0x23,0x5c]
  webserver.addFormSelector("I2C address","plugin_010_addr",2,options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  webserver.addFormCheckBox("Oversampling","plugin_010_over",self.timer2s)
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("plugin_010_addr",params)
  if par == "":
    par = 0
  self.taskdevicepluginconfig[0] = int(par)
  if (webserver.arg("plugin_010_over",params)=="on"):
   self.timer2s = True
  else:
   self.timer2s = False
  return True

 def timer_two_second(self):
  if self.timer2s and self.initialized and self.readinprogress==0 and self.enabled:
   if self._nextdataservetime-rpieTime.millis()<=self.preread:
    self.readinprogress = 1
    self.p010_get_value()
    self.readinprogress = 0
  return self.timer2s

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   self.p010_get_value()
   if len(self.LARR)==1:
    self.set_value(1,self.LARR[0],False)
   if len(self.LARR)>1:
    alux = round((sum(self.LARR) / len(self.LARR)),2)
    if ((max(self.LARR) - min(self.LARR)) > 8): # too much deviation found for light
       difft = abs(max(self.LARR) - alux)
       if (difft > abs(alux-min(self.LARR))):
        difft = abs(alux-min(self.LARR))
       if (difft < 1):
        difft = 1
       if (difft > 10):
        difft = 10
       TARR2 = []
       for i in range(0,len(self.LARR)):
        if (abs(alux-self.LARR[i]) <= difft):
         TARR2.append(self.LARR[i])
       if len(TARR2)>0:
        alux = round((sum(TARR2) / len(TARR2)),2)
    self.set_value(1,alux,False)
   self.plugin_senddata()
#   print(self.LARR)
   self.LARR = []
   self._lastdataservetime = rpieTime.millis()
   self._nextdataservetime = self._lastdataservetime + (self.interval*1000)
   result = True
   self.readinprogress = 0
  return result

 def p010_get_value(self):
   if rpieTime.millis()>=(self.lastread+2000):
    lux = None
    try:
     lux = gpios.HWPorts.i2c_read_block(int(self.taskdevicepluginconfig[0]),0x21,bus=self.i2cbus) # Start measurement at 0.5lx resolution.  Measurement Time is typically 120ms.  It is automatically set to Power Down mode after measurement.
    except:
     lux = None
    if lux != None:
     self.LARR.append(round(self.convertToNumber(lux), 2))
    self.lastread = rpieTime.millis()

 def convertToNumber(self,data):
  res = 0
  if len(data)==1:
   res = data[0]
  elif len(data)>1:
   res = (data[1] + (256 * data[0]))
  return (res / 1.2)
