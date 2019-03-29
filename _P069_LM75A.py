#!/usr/bin/env python3
#############################################################################
######################## LM75A plugin for RPIEasy ###########################
#############################################################################
#
# LM75 code added by haraldtux ( https://github.com/haraldtux )
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import smbus
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 69
 PLUGIN_NAME = "Environment - LM75A (TESTING)"
 PLUGIN_VALUENAME1 = "Temperature"

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
  self.bus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.bus = None
  if self.enabled and int(self.taskdevicepluginconfig[0])>0:
   try:
    i2cok = gpios.HWPorts.i2c_init()
    if i2cok:
     if self.interval>2:
      nextr = self.interval-2
     else:
      nextr = self.interval
     self.bus = gpios.HWPorts.i2cbus
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!")
     self.enabled = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.enabled = False

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x48", "0x49", "0x4a", "0x4b", "0x4c","0x4d", "0x4e", "0x4f"]
  optionvalues = [0x48, 0x49, 0x4a, 0x4b, 0x4c,0x4d, 0x4e, 0x4f]
  webserver.addFormSelector("Address","plugin_069_addr",2,options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  initpar = self.taskdevicepluginconfig[0]
  par = webserver.arg("plugin_069_addr",params)
  if par == "":
   par = 0
  self.taskdevicepluginconfig[0] = int(par)
  if (initpar != self.taskdevicepluginconfig[0]) and (int(self.taskdevicepluginconfig[0])>0):
   self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   atemp = self.read_lm75()
   self.set_value(1,atemp,True)
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def read_lm75(self):
  temp = None
  if self.bus is not None:
   try:
    raw = self.bus.read_word_data(int(self.taskdevicepluginconfig[0]), 0) & 0xFFFF
    raw = ((raw << 8) & 0xFF00) + (raw >> 8)
    temp = (raw / 32.0) / 8.0+ -1.3
   except:
    temp = None
  return temp
