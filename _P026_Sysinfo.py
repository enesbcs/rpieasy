#!/usr/bin/env python3
#############################################################################
############# Generic System Information plugin for RPIEasy #################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import os_os as OS
import misc

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 26
 PLUGIN_NAME = "Generic - System Info"
 PLUGIN_VALUENAME1 = "Value1"
 PLUGIN_VALUENAME2 = "Value2"
 PLUGIN_VALUENAME3 = "Value3"
 PLUGIN_VALUENAME4 = "Value4"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  self.readinprogress = 0
  self.valuecount = 4
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True

 def plugin_init(self,enableplugin=None):
     plugin.PluginProto.plugin_init(self,enableplugin)
     self.initialized = True
     self.readinprogress = 0

 def webform_load(self): # create html page for settings
  try:
   choice1 = int(self.taskdevicepluginconfig[0])
  except:
   choice1 = 0
  try:
   choice2 = int(self.taskdevicepluginconfig[1])
  except:
   choice2 = 0
  try:
   choice3 = int(self.taskdevicepluginconfig[2])
  except:
   choice3 = 0
  try:
   choice4 = int(self.taskdevicepluginconfig[3])
  except:
   choice4 = 0
  try:
   options = ["None","Uptime","Free RAM", "Wifi RSSI","System load","CPU Temp"]
   optionvalues = [0,1,2,3,4,5]
   webserver.addFormSelector("Indicator1","plugin_026_ind0",len(options),options,optionvalues,None,choice1)
   webserver.addFormSelector("Indicator2","plugin_026_ind1",len(options),options,optionvalues,None,choice2)
   webserver.addFormSelector("Indicator3","plugin_026_ind2",len(options),options,optionvalues,None,choice3)
   webserver.addFormSelector("Indicator4","plugin_026_ind3",len(options),options,optionvalues,None,choice4)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"P026 load "+str(e))
  return True

 def webform_save(self,params): # process settings post reply
  try:
   for v in range(0,4):
    par = webserver.arg("plugin_026_ind"+str(v),params)
    if par == "":
     par = 0
    if str(self.taskdevicepluginconfig[v])!=str(par):
     self.uservar[v] = 0
    self.taskdevicepluginconfig[v] = int(par)
    if int(par)>0:
     self.valuecount = (v+1)
  except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"P026 save "+str(e))
  try:
   if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
   elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
   elif self.valuecount == 4:
    self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  except:
   pass
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   try:
    for v in range(0,4):
     vtype = int(self.taskdevicepluginconfig[v])
     if vtype != 0:
      self.set_value(v+1,self.p026_get_value(vtype),False)
    self.plugin_senddata()
    self._lastdataservetime = rpieTime.millis()
    result = True
   except:
    self.readinprogress = 0
   self.readinprogress = 0
  return result

 def p026_get_value(self,ptype):
   value = 0
   try:
    if ptype == 1:
     value = rpieTime.getuptime(0)
    elif ptype == 2:
     value = OS.FreeMem()
    elif ptype == 3:
     value = OS.get_rssi()
    elif ptype == 4:
     value = OS.read_cpu_usage()
    elif ptype == 5:
     value = OS.read_cpu_temp()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"P026 get "+str(e))
   return value
