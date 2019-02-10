#!/usr/bin/env python3
#############################################################################
##################### TSL2561 plugin for RPIEasy ############################
#############################################################################
#
# Plugin based on code from:
# https://github.com/ControlEverythingCommunity/TSL2561/blob/master/Python/TSL2561.py
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# Hardware device for this plugin implementation and testing provided by happytm.
# This plugin would never have been created without happytm! :)
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 15
 PLUGIN_NAME = "Environment - TSL2561 Lux sensor (TESTING)"
 PLUGIN_VALUENAME1 = "Lux"
 PLUGIN_VALUENAME2 = "Infrared"
 PLUGIN_VALUENAME3 = "Fullspectrum"
 DELAY_TIME = [0.015,0.12,0.45]

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  self.readinprogress = 0
  self.valuecount = 3
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
  options = ["0x29","0x39","0x49"]
  optionvalues = [0x29,0x39,0x49]
  webserver.addFormSelector("I2C address","plugin_015_addr",len(options),options,optionvalues,None,int(choice1))
  choice2 = self.taskdevicepluginconfig[1]
  options = ["13.7","101","402"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Exposure speed","plugin_015_spd",len(options),options,optionvalues,None,int(choice2))
  webserver.addUnit("ms")
  choice3 = self.taskdevicepluginconfig[2]
  options = ["1","16"]
  optionvalues = [0,0x10]
  webserver.addFormSelector("Gain","plugin_015_gain",len(options),options,optionvalues,None,int(choice3))
  webserver.addUnit("x")
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("plugin_015_addr",params)
  if par == "":
    par = 0x39
  self.taskdevicepluginconfig[0] = int(par)

  par = webserver.arg("plugin_015_spd",params)
  if par == "":
    par = 0
  self.taskdevicepluginconfig[1] = int(par)

  par = webserver.arg("plugin_015_gain",params)
  if par == "":
    par = 0
  self.taskdevicepluginconfig[2] = int(par)

  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    v1,v2,v3 = self.read_tsl2561()
   except Exception as e:
    v1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"TSL2561: "+str(e))
   if v1 is not None:
    self.set_value(1,v1,False)
    self.set_value(2,v2,False)
    self.set_value(3,v3,False)
    self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def read_tsl2561(self):
  if self.initialized:
   bus = gpios.HWPorts.i2cbus
   v1 = None
   try:
    bus.write_byte_data(int(self.taskdevicepluginconfig[0]), 0x00 | 0x80, 0x03) # 0x03(03) Power ON mode
    cmdcode = int(self.taskdevicepluginconfig[1])+int(self.taskdevicepluginconfig[2])
   except:
    return v1,v1,v1
   time.sleep(0.001)
   try:
    bus.write_byte_data(int(self.taskdevicepluginconfig[0]), 0x01 | 0x80, cmdcode)
    time.sleep(self.DELAY_TIME[int(self.taskdevicepluginconfig[1])])
   except:
    return v1,v1,v1
   data = bus.read_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x0C | 0x80, 2) # read full
   data1 = bus.read_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x0E | 0x80, 2) # read ir
   bus.write_byte_data(int(self.taskdevicepluginconfig[0]), 0x00 | 0x80, 0x00) # 0x00 Power OFF mode
   ch0 = data[1]*256+data[0]
   ch1 = data1[1]*256+data1[0]
   if ch0==0xFFFF or ch1==0xFFFF:
    return v1,v1,v1
   ratio = ch1 / ch0
   d0 = ch0
   d1 = ch1
   if self.taskdevicepluginconfig[2]==0:
    ch0 = ch0 * 16
    ch1 = ch1 * 16
   lux = 0
   if (ratio < 0.5):
    lux = 0.0304 * ch0 - 0.062 * ch0 * pow(ratio,1.4)
   elif (ratio < 0.61):
    lux = 0.0224 * ch0 - 0.031 * ch1
   elif (ratio < 0.80):
    lux = 0.0128 * ch0 - 0.0153 * ch1
   elif (ratio < 1.30):
    lux = 0.00146 * ch0 - 0.00112 * ch1
   if lux<0:
    lux = 0
   return lux,d1,d0
