#!/usr/bin/env python3
#############################################################################
####################### SHT30 plugin for RPIEasy ############################
#############################################################################
#
# Plugin based on code from:
# https://github.com/ControlEverythingCommunity/SHT30/blob/master/Python/SHT30.py
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 68
 PLUGIN_NAME = "Environment - SHT30 temperature sensor (TESTING)"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Humidity"

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

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  if self.enabled:
   try:
    i2cok = gpios.HWPorts.i2c_init()
    if i2cok:
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

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x44","0x45"]
  optionvalues = [0x44,0x45]
  webserver.addFormSelector("I2C address","plugin_68_addr",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("plugin_68_addr",params)
  if par == "":
    par = 0x44
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    temp, hum = self.read_sht30()
   except Exception as e:
    temp = None
    hum = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SHT30: "+str(e))
   if temp is not None:
    self.set_value(1,temp,False)
    self.set_value(2,hum,False)
    self.plugin_senddata()
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def read_sht30(self):
  if self.initialized:
   bus = gpios.HWPorts.i2cbus
   temp = None
   hum = None
   try:
    bus.write_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x2C, [0x06]) # send measure command, high repeatability
    time.sleep(0.1)
    data = bus.read_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x00, 6) # read data
    temp = ((((data[0] * 256.0) + data[1]) * 175) / 65535.0) - 45
    hum  = 100 * (data[3] * 256 + data[4]) / 65535.0
   except:
    return None, None
   return temp, hum
