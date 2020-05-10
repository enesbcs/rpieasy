#!/usr/bin/env python3
#############################################################################
###################### Dummy plugin for RPIEasy #############################
#############################################################################
#
# Generic device for script aiding such as holding global variables.
# Two way communication is implemented through plugin_receivedata()
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 33
 PLUGIN_NAME = "Generic - Dummy Device"
 PLUGIN_VALUENAME1 = "Dummy1"
 PLUGIN_VALUENAME2 = "Dummy2"
 PLUGIN_VALUENAME3 = "Dummy3"
 PLUGIN_VALUENAME4 = "Dummy4"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 4
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.recdataoption = True
  self.formulaoption = True

 def plugin_receivedata(self,data):
  if (len(data)>0):
   for x in range(len(data)):
    if data[x] != -9999:
     self.set_value(x+1,data[x],False)
#  print("Data received:",data)

 def getvaluecount(self):
   if self.vtype in [rpieGlobals.SENSOR_TYPE_SINGLE,rpieGlobals.SENSOR_TYPE_SWITCH,rpieGlobals.SENSOR_TYPE_DIMMER,rpieGlobals.SENSOR_TYPE_LONG,rpieGlobals.SENSOR_TYPE_WIND]:
    return 1
   elif self.vtype in [rpieGlobals.SENSOR_TYPE_TEMP_HUM,rpieGlobals.SENSOR_TYPE_TEMP_BARO,rpieGlobals.SENSOR_TYPE_DUAL]:
    return 2
   elif self.vtype in [rpieGlobals.SENSOR_TYPE_TEMP_HUM_BARO,rpieGlobals.SENSOR_TYPE_TRIPLE]:
    return 3
   elif self.vtype == rpieGlobals.SENSOR_TYPE_QUAD:
    return 4
   else:
    return 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.taskdevicepluginconfig[0]>0:
    self.vtype = self.taskdevicepluginconfig[0]
    self.valuecount = self.getvaluecount()
    self.initialized = True

 def webform_load(self): # create html page for settings
  choice = self.taskdevicepluginconfig[0]
  options = ["Single","Hum","Baro","Hum+Baro","Dual","Triple","Quad","Switch","Dimmer","Long","Wind"]
  optionvalues = [rpieGlobals.SENSOR_TYPE_SINGLE, rpieGlobals.SENSOR_TYPE_TEMP_HUM,rpieGlobals.SENSOR_TYPE_TEMP_BARO,rpieGlobals.SENSOR_TYPE_TEMP_HUM_BARO,rpieGlobals.SENSOR_TYPE_DUAL,rpieGlobals.SENSOR_TYPE_TRIPLE,rpieGlobals.SENSOR_TYPE_QUAD,rpieGlobals.SENSOR_TYPE_SWITCH,rpieGlobals.SENSOR_TYPE_DIMMER,rpieGlobals.SENSOR_TYPE_LONG,rpieGlobals.SENSOR_TYPE_WIND]
  webserver.addFormSelector("Simulate Data Type","plugin_033_sensortype",11,options,optionvalues,None,choice)
  return True

 def webform_save(self,params): # process settings post reply
  par1 = webserver.arg("plugin_033_sensortype",params)
  if par1:
   self.taskdevicepluginconfig[0] = int(par1)
   self.vtype = self.taskdevicepluginconfig[0]
   self.valuecount = self.getvaluecount()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized:
   for x in range(self.valuecount):
    logs = self.gettaskname()+"#"+self.valuenames[x]+"="+str(misc.formatnum(self.uservar[x],self.decimals[x]))
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,logs)
   self._lastdataservetime = rpieTime.millis()
   self.plugin_senddata()
   result = True
  return result
