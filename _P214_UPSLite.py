#!/usr/bin/env python3
#############################################################################
####################### UPS-Lite plugin for RPIEasy #########################
#############################################################################
#
# Based on https://github.com/linshuqin329/UPS-Lite/blob/master/UPS_Lite.py
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import smbus
import time
import struct

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 214
 PLUGIN_NAME = "Energy (DC) - UPS-Lite - MAX17040"
 PLUGIN_VALUENAME1 = "Voltage"
 PLUGIN_VALUENAME2 = "Capacity"
 ADDR=0x36

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  self.readinprogress = 0
  self.valuecount = 2
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.i2cbus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled:
   if self.valuecount == 1:
     self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   elif self.valuecount == 2:
     self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
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
     try:
      self.readinprogress=0
      self.QuickStart()
      self.initialized = True
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"UPSLite init failed: "+str(e))
      self.initialized = False
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!")
     self.initialized = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.initialized = False
    self.i2cbus = None

 def webform_load(self): # create html page for settings
  webserver.addFormNote("I2C address is fixed 0x36! You can check it at <a href='i2cscanner'>i2cscan</a> page.")
  if self.taskname=="":
   choice1 = 0
   choice2 = 1
  else:
   choice1 = self.taskdevicepluginconfig[0]
   choice2 = self.taskdevicepluginconfig[1]
  options = ["None", "Voltage","Capacity"]
  optionvalues = [-1, 2, 4]
  webserver.addFormSelector("Indicator1","plugin_214_ind0",len(options),options,optionvalues,None,choice1)
  webserver.addFormSelector("Indicator2","plugin_214_ind1",len(options),options,optionvalues,None,choice2)
  return True

 def webform_save(self,params): # process settings post reply
  try:
   for v in range(0,2):
    par = webserver.arg("plugin_214_ind"+str(v),params)
    if par == "":
     par = -1
    else:
     par=int(par)
    if str(self.taskdevicepluginconfig[v])!=str(par):
     self.uservar[v] = 0
    self.taskdevicepluginconfig[v] = par
    if int(par)>0 and self.valuecount!=v+1:
     self.valuecount = (v+1)
   if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,+str(e))
  self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   for v in range(0,2):
      vtype = int(self.taskdevicepluginconfig[v])
      try:
       if vtype == 2:
         value = self.readVoltage()
         if value != None:
          self.set_value(v+1,value,False)
       elif vtype ==4:
         value = self.readCapacity()
         if value != None:
          self.set_value(v+1,value,False)
      except Exception as e:
       value = None
   self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def readVoltage(self):
        read = self.i2cbus.read_word_data(self.ADDR, 0X02)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        voltage = swapped * 1.25 /1000/16
        return voltage

 def readCapacity(self):
        read = self.i2cbus.read_word_data(self.ADDR, 0X04)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        capacity = swapped/256
        return capacity

 def QuickStart(self):
        self.i2cbus.write_word_data(self.ADDR, 0x06,0x4000)

 def PowerOnReset(self):
        self.i2cbus.write_word_data(self.ADDR, 0xfe,0x0054)
