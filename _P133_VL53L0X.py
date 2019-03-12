#!/usr/bin/env python3
#############################################################################
##################### VL53L0X plugin for RPIEasy ############################
#############################################################################
#
# Plugin for using VL53L0X I2C ranging LIDAR sensor
#
# Based on Dexter Industries Sensors:
#  https://github.com/DexterInd/DI_Sensors/blob/master/Python/di_sensors/VL53L0X.py
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import lib.vl53l0x.vl53l0x as VL53L0X

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 133
 PLUGIN_NAME = "Distance - VL53L0X sensor (TESTING)"
 PLUGIN_VALUENAME1 = "mm"

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
  self.vl = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
  if self.enabled:
   i2cport = -1
   try:
    for i in range(0,2):
     if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
      i2cport = i
      break
   except:
    i2cport = -1
   e = ""
   if i2cport>-1:
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval
    self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    try:
     if int(self.taskdevicepluginconfig[0])>0:
      self.vl = VL53L0X.VL53L0X(busnum=i2cport,i2c_address=int(self.taskdevicepluginconfig[0]))
      self.initialized = self.vl.initialized
    except Exception as e:
     self.initialized = False
   if self.initialized == False:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"VL53L0X can not be initialized! "+str(e))

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x29","0x30"]
  optionvalues = [0x29,0x30]
  webserver.addFormSelector("I2C address","plugin_133_addr",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("plugin_133_addr",params)
  if par == "":
    par = 0x29
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    val1 = self.vl.read_range_single_millimeters()
   except Exception as e:
    val1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"VL53L0X: "+str(e))
   if val1 is not None:
    self.set_value(1,val1,True)
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result
