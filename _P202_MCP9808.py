#!/usr/bin/env python3
#############################################################################
######################## MCP9808 plugin for RPIEasy #########################
#############################################################################
#
# MCP9808 code based on:
#  https://github.com/ControlEverythingCommunity/MCP9808/blob/master/Python/MCP9808.py
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
 PLUGIN_ID = 202
 PLUGIN_NAME = "Environment - MCP9808 (TESTING)"
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
  self.initialized = False
  self.readinprogress=0
  if self.enabled and int(self.taskdevicepluginconfig[0])>0:
   try:
    i2cok = gpios.HWPorts.i2c_init()
    if i2cok:
     if self.interval>2:
      nextr = self.interval-2
     else:
      nextr = self.interval
     self.bus = gpios.HWPorts.i2cbus
     config = [0x00, 0x00]
     self.bus.write_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x01, config) # Select configuration register, 0x01(1) 0x0000(00)	Continuous conversion mode, Power-up default
     self.bus.write_byte_data(int(self.taskdevicepluginconfig[0]), 0x08, 0x03)        # Select resolution register, 0x08(8) 0x03(03)	Resolution = +0.0625 / C !!! MAX 4 TIMES/SEC!!!
     self.initialized = True
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!")
     self.enabled = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MCP9808 init failed "+str(e))
    self.enabled = False

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x18", "0x19", "0x1a", "0x1b", "0x1c","0x1d", "0x1e", "0x1f"]
  optionvalues = [0x18, 0x19, 0x1a, 0x1b, 0x1c,0x1d, 0x1e, 0x1f]
  webserver.addFormSelector("Address","plugin_202_addr",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  initpar = self.taskdevicepluginconfig[0]
  par = webserver.arg("plugin_202_addr",params)
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
   atemp = self.read_mcp9808()
   if atemp is not None:
    self.set_value(1,atemp,True)
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def read_mcp9808(self):
  temp = None
  if self.bus is not None:
   try:
    data = self.bus.read_i2c_block_data(int(self.taskdevicepluginconfig[0]), 0x05, 2)
    ctemp = ((data[0] & 0x1F) * 256) + data[1]
    if ctemp > 4095:
     ctemp -= 8192
    temp = ctemp * 0.0625
   except:
    temp = None
  return temp
