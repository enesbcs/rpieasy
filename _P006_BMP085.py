#!/usr/bin/env python3
#############################################################################
###################### BMP085/180 plugin for RPIEasy ########################
#############################################################################
#
# Plugin based on code from:
# https://github.com/ControlEverythingCommunity/BMP180/blob/master/Python/BMP180.py
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 6
 PLUGIN_NAME = "Environment - BMP085/180 (TESTING)"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Pressure"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_EMPTY_BARO
  self.readinprogress = 0
  self.valuecount = 2
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.bmp = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.uservar[1] = 0
  self.initialized = False
  if self.enabled:
   try:
    self.bmp = None
    try:
     i2cl = self.i2c
    except:
     i2cl = -1
    if i2cl==-1:
     i2cbus = gpios.HWPorts.i2cbus
    else:
     i2cbus = gpios.HWPorts.i2c_init(i2cl)
    sensoraddress = int(self.taskdevicepluginconfig[0])
    self.bmp = Bmp180(i2c_bus=i2cbus,sensor_address=sensoraddress)
    if (self.bmp is not None) and (i2cbus is not None) and self.bmp.init:
     if self.interval>2:
      nextr = self.interval-2
     else:
      nextr = self.interval
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
     self.lastread = 0
     self.initialized = True
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BMP180 can not be initialized!")
     self.initialized = False
    self.readinprogress = 0
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.initialized = False
    self.bmp = None
    self.readinprogress = 0

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x77"]
  optionvalues = [0x77]
  webserver.addFormSelector("I2C address","plugin_6_addr",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("plugin_6_addr",params)
  if par == "":
    par = 0x77
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   temp, press = self.bmp.get_data()
   self.set_value(1,temp,False)
   self.set_value(2,press,False)
   self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

class Bmp180(object):
 ADDR = 0x77

 def __init__(self, i2c_bus=None, sensor_address=ADDR):
      self.init = False
      if i2c_bus != None:
       try:
        self.bus = i2c_bus
        self.sensor_address = sensor_address
        self.read_calibration_parameters()
        self.init = True
       except Exception as e:
#        print("BMP180 init err ",e)
        self.bus = None

 def read_calibration_parameters(self):
    # BMP180 address, 0x77(119)
    # Read data back from 0xAA(170), 22 bytes
    data = self.bus.read_i2c_block_data(self.sensor_address, 0xAA, 22)
    # Convert the data
    self.AC1 = data[0] * 256 + data[1]
    if self.AC1 > 32767 :
        self.AC1 -= 65535
    self.AC2 = data[2] * 256 + data[3]
    if self.AC2 > 32767 :
        self.AC2 -= 65535
    self.AC3 = data[4] * 256 + data[5]
    if self.AC3 > 32767 :
        self.AC3 -= 65535
    self.AC4 = data[6] * 256 + data[7]
    self.AC5 = data[8] * 256 + data[9]
    self.AC6 = data[10] * 256 + data[11]
    self.B1 = data[12] * 256 + data[13]
    if self.B1 > 32767 :
        self.B1 -= 65535
    self.B2 = data[14] * 256 + data[15]
    if self.B2 > 32767 :
        self.B2 -= 65535
    self.MB = data[16] * 256 + data[17]
    if self.MB > 32767 :
        self.MB -= 65535
    self.MC = data[18] * 256 + data[19]
    if self.MC > 32767 :
        self.MC -= 65535
    self.MD = data[20] * 256 + data[21]
    if self.MD > 32767 :
        self.MD -= 65535

 def get_data(self):
  if self.init:
   cTemp = None
   pressure = None
   try:
    # BMP180 address, 0x77(119)
    # Select measurement control register, 0xF4(244)
    #		0x2E(46)	Enable temperature measurement
    self.bus.write_byte_data(self.sensor_address, 0xF4, 0x2E)
    time.sleep(0.01)
    # BMP180 address, 0x77(119)
    # Read data back from 0xF6(246), 2 bytes
    # temp MSB, temp LSB
    data = self.bus.read_i2c_block_data(self.sensor_address, 0xF6, 2)
    # Convert the data
    temp = data[0] * 256 + data[1]
    # BMP180 address, 0x77(119)
    # Select measurement control register, 0xF4(244)
    #		0x74(116)	Enable pressure measurement, OSS = 1
    self.bus.write_byte_data(self.sensor_address, 0xF4, 0x74)
    time.sleep(0.026)
    # BMP180 address, 0x77(119)
    # Read data back from 0xF6(246), 3 bytes
    # pres MSB1, pres MSB, pres LSB
    data = self.bus.read_i2c_block_data(self.sensor_address, 0xF6, 3)
    # Convert the data
    pres = ((data[0] * 65536) + (data[1] * 256) + data[2]) / 128
    # Callibration for Temperature
    X1 = (temp - self.AC6) * self.AC5 / 32768.0
    X2 = (self.MC * 2048.0) / (X1 + self.MD)
    B5 = X1 + X2
    cTemp = ((B5 + 8.0) / 16.0) / 10.0
    # Calibration for Pressure
    B6 = B5 - 4000
    X1 = (self.B2 * (B6 * B6 / 4096.0)) / 2048.0
    X2 = self.AC2 * B6 / 2048.0
    X3 = X1 + X2
    B3 = (((self.AC1 * 4 + X3) * 2) + 2) / 4.0
    X1 = self.AC3 * B6 / 8192.0
    X2 = (self.B1 * (B6 * B6 / 2048.0)) / 65536.0
    X3 = ((X1 + X2) + 2) / 4.0
    B4 = self.AC4 * (X3 + 32768) / 32768.0
    B7 = ((pres - B3) * (25000.0))
    pressure = 0.0
    if B7 < 2147483648:
        pressure = (B7 * 2) / B4
    else :
        pressure = (B7 / B4) * 2
    X1 = (pressure / 256.0) * (pressure / 256.0)
    X1 = (X1 * 3038.0) / 65536.0
    X2 = ((-7357) * pressure) / 65536.0
    pressure = (pressure + (X1 + X2 + 3791) / 16.0) / 100
    # Calculate Altitude
    altitude = 44330 * (1 - ((pressure / 1013.25) ** 0.1903))
   except Exception as e:
#    print("BMP180 read err",e)#debug
    return None, None
   return cTemp, pressure
