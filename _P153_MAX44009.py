#!/usr/bin/env python3
#############################################################################
##################### MAX44009 plugin for RPIEasy ###########################
#############################################################################
#
# Plugin based on code from:
# https://github.com/ControlEverythingCommunity/MAX44009/blob/master/Python/MAX44009.py
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
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
 PLUGIN_ID = 153
 PLUGIN_NAME = "Environment - MAX44009 ambient light sensor (TESTING)"
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
  self.i2cbus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
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
     self.initialized = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.initialized = False
    self.i2cbus = None

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x4A"]
  optionvalues = [0x4A]
  webserver.addFormSelector("I2C address","plugin_153_addr",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("plugin_153_addr",params)
  if par == "":
    par = 0x4A
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    val1 = self.read_max44009()
   except Exception as e:
    val1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MAX44009: "+str(e))
   if val1 is not None:
    self.set_value(1,val1,True)
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def read_max44009(self):
  if self.initialized:
   try:
    bus = self.i2cbus
   except:
    self.i2cbus = None
    return None
   v1 = None
   try:
    bus.write_byte_data(int(self.taskdevicepluginconfig[0]), 0x02, 0x40) # Select configuration register, 0x02(02), 0x40(64) Continuous mode, Integration time = 800 ms
    time.sleep(0.5)
    data = bus.read_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x03, 2)  # Read data back from 0x03(03), 2 bytes, luminance MSB, luminance LSB
    exponent = (data[0] & 0xF0) >> 4
    mantissa = ((data[0] & 0x0F) << 4) | (data[1] & 0x0F)
    luminance = ((2 ** exponent) * mantissa) * 0.045
   except:
    return v1
   return luminance
