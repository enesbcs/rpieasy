#!/usr/bin/env python3
#############################################################################
####################### BME680 plugin for RPIEasy ###########################
#############################################################################
#
# Copyright (C) 2023 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import lib.lib_bme680router as bmerouter

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 106
 PLUGIN_NAME = "Environment - BME680"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Humidity"
 PLUGIN_VALUENAME3 = "Pressure"
 PLUGIN_VALUENAME4 = "Gas"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  self.readinprogress = 0
  self.valuecount = 4
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.bme = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
  if self.enabled:
   try:
     i2cl = self.i2c
   except:
     i2cl = -1
   try:
    i2cport = gpios.HWPorts.geti2clist()
    if i2cl==-1:
      i2cl = int(i2cport[0])
   except:
    i2cport = []
   if len(i2cport)>0 and i2cl>-1:
     try:
      dport = int(self.taskdevicepluginconfig[0])
     except:
      dport = 0
     if dport == 0:
      dport = 0x77
      self.bme = None
     try:
      self.bme = bmerouter.request_bme_device(busnum=int(i2cl),i2caddress=dport)
      self.initialized = True
     except Exception as e:
      self.bme = None
   if self.bme is None:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BME680 can not be initialized! ")
    return False

 def webform_load(self): # create html page for settings
  choice0 = self.taskdevicepluginconfig[0]
  options = ["0x77","0x76"]
  optionvalues = [0x77,0x76]
  webserver.addFormSelector("I2C address","plugin_106_addr",len(optionvalues),options,optionvalues,None,int(choice0))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  options = ["None","Temperature","Humidity","Pressure","Gas"]
  optionvalues = [0,1,2,3,4]
  try:
   choice1 = int(self.taskdevicepluginconfig[1])
  except:
   choice1 = 1
  try:
   choice2 = int(self.taskdevicepluginconfig[2])
  except:
   choice2 = 2
  try:
   choice3 = int(self.taskdevicepluginconfig[3])
  except:
   choice3 = 3
  try:
   choice4 = int(self.taskdevicepluginconfig[4])
  except:
   choice3 = 4

  webserver.addFormSelector("Value 1","plugin_106_v1",len(options),options,optionvalues,None,int(choice1))
  webserver.addFormSelector("Value 2","plugin_106_v2",len(options),options,optionvalues,None,int(choice2))
  webserver.addFormSelector("Value 3","plugin_106_v3",len(options),options,optionvalues,None,int(choice3))
  webserver.addFormSelector("Value 4","plugin_106_v4",len(options),options,optionvalues,None,int(choice4))
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("plugin_106_addr",params)
   if par == "":
    par = 0x77
   self.taskdevicepluginconfig[0] = int(par)

   try:
    for v in range(1,5):
     par = webserver.arg("plugin_106_v"+str(v),params)
     if par == "":
      par = 0
     if str(self.taskdevicepluginconfig[v])!=str(par):
      self.uservar[v-1] = 0
     self.taskdevicepluginconfig[v] = int(par)
     if int(par)>0:
      self.valuecount = v
   except Exception as e:
     pass
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
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    vals = self.bme.read()
    for v in range(1,5):
     try:
      vtype = int(self.taskdevicepluginconfig[v])
     except:
      vtype = 0
     if vtype != 0:
      self.set_value(v,self.p106_get_value(vals,vtype),False)
    self.plugin_senddata()
    self._lastdataservetime = rpieTime.millis()
   except Exception as e:
    val1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BME680: "+str(e))
   result = True
   self.readinprogress = 0
  return result

 def p106_get_value(self,valdict,ptype):
   value = 0
   try:
    if ptype == 1:
     value = valdict['temperature']
    elif ptype == 2:
     value = valdict['humidity']
    elif ptype == 3:
     value = valdict['pressure']
    elif ptype == 4:
     value = valdict['gas']
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"P106 get "+str(e))
   return value
