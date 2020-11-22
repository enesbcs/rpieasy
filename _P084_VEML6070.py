#!/usr/bin/env python3
#############################################################################
##################### VEML6070 plugin for RPIEasy ###########################
#############################################################################
#
# Based on original ESPEasy P084 plugin
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
 PLUGIN_ID = 84
 PLUGIN_NAME = "Environment - VEML6070 UV sensor (TESTING)"
 PLUGIN_VALUENAME1 = "UV-Raw"
 PLUGIN_VALUENAME2 = "UV-Risk"
 PLUGIN_VALUENAME3 = "UV-Power"
 VEML6070_ADDR_H             = 0x39
 VEML6070_ADDR_L             = 0x38
 VEML6070_RSET_DEFAULT       = 270000      # 270K default resistor value 270000 ohm, range from 220K..1Meg
 VEML6070_UV_MAX_INDEX       = 15          # normal 11, internal on weather laboratories and NASA it's 15 so far the sensor is linear
 VEML6070_UV_MAX_DEFAULT     = 11          # 11 = public default table values
 VEML6070_POWER_COEFFCIENT   = 0.025       # based on calculations from Karel Vanicek and reorder by hand
 VEML6070_TABLE_COEFFCIENT   = 32.86270591
 VEML6070_base_value = ((VEML6070_RSET_DEFAULT / VEML6070_TABLE_COEFFCIENT) / VEML6070_UV_MAX_DEFAULT) * (1)
 VEML6070_max_value  = ((VEML6070_RSET_DEFAULT / VEML6070_TABLE_COEFFCIENT) / VEML6070_UV_MAX_DEFAULT) * (VEML6070_UV_MAX_INDEX)

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
  self.i2cbus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.readinprogress = 0
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
     self.i2cbus.write_byte(self.VEML6070_ADDR_L, (( self.taskdevicepluginconfig[0] << 2) | 0x02)) # init veml
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!")
     self.initialized = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.initialized = False
    self.i2cbus = None

 def webform_load(self): # create html page for settings
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  choice1 = self.taskdevicepluginconfig[0]
  options = ["1/2T","1T","2T","4T"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Refresh Time Determination","itime",len(options),options,optionvalues,None,int(choice1))
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("itime",params)
  if par == "":
    par = 4
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    raw = self.VEML6070_readraw()
   except Exception as e:
    raw = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"VEML6070: "+str(e))
   if raw is not None:
    self.set_value(1,raw,False)
    risk = self.VEML6070_uvrisklevel(raw)
    self.set_value(2,risk,False)
    self.set_value(3,self.VEML6070_uvpower(risk),False)
    self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def VEML6070_readraw(self):
     uv_raw = 0
     try:
      data1 = self.i2cbus.read_byte(self.VEML6070_ADDR_H)
      data0 = self.i2cbus.read_byte(self.VEML6070_ADDR_L)
      uv_raw = data1*256 + data0
     except Exception as e:
      pass
     return uv_raw

 def VEML6070_uvrisklevel(self,uv_level):
     risk = 0
     if (uv_level < self.VEML6070_max_value):
      return (uv_level / self.VEML6070_base_value)
     else:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"VEML6070 out of range: "+str(uv_level))
     return 99

 def VEML6070_uvpower(self,uvrisk):
     return (self.VEML6070_POWER_COEFFCIENT * uvrisk)
