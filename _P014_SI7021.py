#!/usr/bin/env python3
#############################################################################
##################### SI7021/HTU21D plugin for RPIEasy ######################
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
import fcntl # smbus does not work properly with HTU21... we need direct i2c access
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 14
 PLUGIN_NAME = "Environment - SI7021/HTU21D"
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
  self.htu = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.uservar[1] = 0
  if self.enabled:
   i2cport = -1
   try:
    for i in range(0,2):
     if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
      i2cport = i
      break
   except:
    i2cport = -1
   if i2cport>-1:
     self.htu = None
     try:
      self.htu = HTU21D(i2cport)
     except Exception as e:
      self.htu = None
   if self.htu:
    try:
     self.initialized = self.htu.init
    except:
     self.htu = None
   if self.htu is None:
    self.initialized = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HTU21D/Si7021 can not be initialized! "+str(e))

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   try:
    temp = self.htu.read_temperature()
    hum  = self.htu.read_humidity()
    self.set_value(1,temp,False)
    self.set_value(2,hum,False)
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HTU21 read error! "+str(e))
    self.enabled = False
   self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result


class HTU21D:
    #control constants
    _I2C_ADDRESS = 0x40

    _SOFTRESET = bytes([0xFE])
    _TRIGGER_TEMPERATURE_NO_HOLD = bytes([0xF3])
    _TRIGGER_HUMIDITY_NO_HOLD = bytes([0xF5])

    #From: /linux/i2c-dev.h
    I2C_SLAVE = 0x0703
    I2C_SLAVE_FORCE = 0x0706

    def __init__(self, device_number=1):
     try:
      self.i2cr = open("/dev/i2c-"+str(device_number),"rb",buffering=0)
      self.i2cw = open("/dev/i2c-"+str(device_number),"wb",buffering=0)
      fcntl.ioctl(self.i2cr, self.I2C_SLAVE,0x40) # I2CADDR
      fcntl.ioctl(self.i2cw, self.I2C_SLAVE,0x40) # I2CADDR
      self.i2cw.write(self._SOFTRESET)
      time.sleep(0.015)
      self.init = True
     except:
      self.init = False

    def read_temperature(self):
     if self.init:
      self.i2cw.write(self._TRIGGER_TEMPERATURE_NO_HOLD)
      time.sleep(0.050)
      data = self.i2cr.read(3)
      return self._get_temperature_from_buffer(data)

    def read_humidity(self):
     if self.init:
      self.i2cw.write(self._TRIGGER_HUMIDITY_NO_HOLD)
      time.sleep(0.025)
      data = self.i2cr.read(3)
      return self._get_humidity_from_buffer(data)

    def close(self):
     if self.init:
      self.i2cr.close()
      self.i2cw.close()

    def __enter__(self):
     return self

    def __exit__(self, type, value, traceback):
     self.close()

    def _get_temperature_from_buffer(self, data):
     if len(data)>1:
      raw = (data[0] << 8) + data[1]
      raw *= 175.72
      raw /= 1 << 16
      raw -= 46.85
     else:
      raw = 0
     return raw

    def _get_humidity_from_buffer(self, data):
     if len(data)>1:
      raw = (data[0] << 8) + data[1]
      raw *= 125.0
      raw /= 1 << 16
      raw -= 6
     else:
      raw = 0
     return raw
