#!/usr/bin/env python3
#############################################################################
##################### BLE Mi Flora plugin for RPIEasy #######################
#############################################################################
#
# Xiaomi Mi Flora Bluetooth plant sensor plugin.
# Can be used when BLE compatible Bluetooth dongle and BluePy is installed.
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import lib.lib_miflora as MiFloraMonitor

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 515
 PLUGIN_NAME = "Environment - BLE Xiaomi Mi Flora (TESTING)"
 PLUGIN_VALUENAME1 = "Temperature"               # Temperature/Brightness/Moisture/Conductivity

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_BLE
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.flora = None
  self.readinprogress=0
  self.initialized=False
  self.failures = 0

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Device Address","plugin_515_addr",str(self.taskdevicepluginconfig[0]),20)
  webserver.addFormNote("Enable blueetooth then <a href='blescanner'>scan 'Flower care' address</a> first.")
  choice1 = self.taskdevicepluginconfig[1]
  choice2 = self.taskdevicepluginconfig[2]
  choice3 = self.taskdevicepluginconfig[3]
  choice4 = self.taskdevicepluginconfig[4]
  options = ["None","Temperature","Brightness", "Moisture","Conductivity","Battery"]
  optionvalues = [0,1,2,3,4,5]
  webserver.addFormSelector("Indicator1","plugin_515_ind0",len(options),options,optionvalues,None,choice1)
  webserver.addFormSelector("Indicator2","plugin_515_ind1",len(options),options,optionvalues,None,choice2)
  webserver.addFormSelector("Indicator3","plugin_515_ind2",len(options),options,optionvalues,None,choice3)
  webserver.addFormSelector("Indicator4","plugin_515_ind3",len(options),options,optionvalues,None,choice4)
  return True

 def webform_save(self,params): # process settings post reply
  try:
   self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_515_addr",params)).strip()
   for v in range(0,4):
    par = webserver.arg("plugin_515_ind"+str(v),params)
    if par == "":
     par = 0
    else:
     par=int(par)
    if str(self.taskdevicepluginconfig[v+1])!=str(par):
     self.uservar[v] = 0
    self.taskdevicepluginconfig[v+1] = par
    options = ["None","Temperature","Brightness", "Moisture","Conductivity","Battery"]
    if int(par)>0 and self.valuecount!=v+1:
     self.valuecount = (v+1)
     self.valuenames[v]=options[par]
   if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
   elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
   elif self.valuecount == 4:
    self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,+str(e))
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.taskdevicepluginconfig[0] = str(self.taskdevicepluginconfig[0]).strip()
  self.readinprogress=0
  self.initialized=False
  if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  elif self.valuecount == 4:
    self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  if self.enabled and self.taskdevicepluginconfig[0]!="" and self.taskdevicepluginconfig[0]!="0":
   try:
    if self.interval<60:
     to = self.interval
    else:
     to = 60
    self.flora = MiFloraMonitor.request_flora_device(str(self.taskdevicepluginconfig[0]),to)
    fv = self.flora.firmware_version()
    if fv!="":
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MiFlora v"+str(fv)+" connected, address: "+str(self.taskdevicepluginconfig[0]))
     self.initialized=True
     self.failures = 0
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MiFlora connection failed, address: "+str(self.taskdevicepluginconfig[0]))
     self.uservar[1] = 0
     self.uservar[2] = 0
     self.uservar[3] = 0
     self.set_value(1,0,True,suserssi=-100,susebattery=0)
   except Exception as e:
    self.failures += 1
    self.flora = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MiFlora error: "+str(e))

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   try:
    batt = self.flora.battery_level()
   except:
    batt = 255
   for v in range(0,4):
    vtype = int(self.taskdevicepluginconfig[v+1])
    if vtype != 0:
     self.set_value(v+1,self.p515_get_value(vtype),False,susebattery=batt)
   self.plugin_senddata(pusebattery=batt)
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def p515_get_value(self,ptype):
  value = 0
  try: 
   if ptype == 1:
    value = self.flora.get_temperature()
   elif ptype == 2:
    value = self.flora.get_light()
   elif ptype == 3:
    value = self.flora.get_moisture()
   elif ptype == 4:
    value = self.flora.get_conductivity()
   elif ptype == 5:
    value = self.flora.battery_level()
  except Exception as e:
    self.failures += 1
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MiFlora error: "+str(e))
    if self.failures>5:
     self.enabled=False
  return value
