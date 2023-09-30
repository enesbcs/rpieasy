#!/usr/bin/env python3
#############################################################################
##################### Pulse counter plugin for RPIEasy ######################
#############################################################################
#
# Based on the original ESPEasy P003 plugin.
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import webserver

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 3
 PLUGIN_NAME = "Input - Pulse Counter"
 PLUGIN_VALUENAME1 = "Count"
 PLUGIN_VALUENAME2 = "Total"
 PLUGIN_VALUENAME3 = "Time"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SINGLE
  self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  self.valuecount = 3
  self.senddataoption = True
  self.timeroption = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.pulsecounter = 0
  self.pulsetotalcounter = 0
  self.pulsetime = 0
  self.pulsetimeprevious = 0
  self.timer100ms = False
  self.readinprogress = False
  self.irqinprogress = False
  self.prevval = -1
  self.formulaoption = True

 def webform_load(self): # create html page for settings
  webserver.addFormNote("Select an input pin.")
  webserver.addFormNumericBox("Debounce Time (mSec)","p003",self.taskdevicepluginconfig[0])
  choice1 = self.taskdevicepluginconfig[1]
  options = ["Delta","Delta/Total/Time","Total","Delta/Total"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Counter Type","p003_countertype",len(options),options,optionvalues,None,choice1)
  choice2 = self.taskdevicepluginconfig[2]
  options = ["BOTH","RISING","FALLING"]
  optionvalues = [gpios.BOTH,gpios.RISING,gpios.FALLING]
  webserver.addFormSelector("Mode Type","p003_raisetype",len(options),options,optionvalues,None,choice2)
  return True

 def webform_save(self,params): # process settings post reply
  pchanged = False
  par1 = webserver.arg("p003",params)
  try:
   self.taskdevicepluginconfig[0] = int(par1)
  except:
   self.taskdevicepluginconfig[0] = 0
  par1 = webserver.arg("p003_countertype",params)
  try:
   if str(self.taskdevicepluginconfig[1]) != str(par1):
    self.taskdevicepluginconfig[1] = int(par1)
    pchanged = True
  except:
   self.taskdevicepluginconfig[1] = 0
  par1 = webserver.arg("p003_raisetype",params)
  try:
   if str(self.taskdevicepluginconfig[2]) != str(par1):
    self.taskdevicepluginconfig[2] = int(par1)
    pchanged = True
  except:
   self.taskdevicepluginconfig[2] = 0
  if pchanged:
   self.plugin_init()
  return True

 def __del__(self):
  try:
   gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
  except: 
   pass

 def plugin_exit(self):
  self.__del__()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.decimals[1]=0
  self.decimals[2]=0
  self.initialized=False
  try:
   self.prevval = -1
  except:
   self.prevval = -1
  if self.enabled and self.taskdevicepin[0]>0:
   self.__del__()
   self.readinprogress = False
   self.pulsecounter = 0
   self.pulsetimeprevious = rpieTime.millis()
   self.irqinprogress = False
   time.sleep(0.1)
   try:
    gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),self.taskdevicepluginconfig[2],self.p003_handler)
    self.initialized = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"GPIO event handlers can not be created "+str(e))
   if self.initialized:
    if self.taskdevicepluginconfig[1] == 0:
     self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
    elif self.taskdevicepluginconfig[1] == 1:
     self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
    elif self.taskdevicepluginconfig[1] == 2:
     self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
    elif self.taskdevicepluginconfig[1] == 3:
     self.vtype = rpieGlobals.SENSOR_TYPE_DUAL

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled:
    if self.taskdevicepluginconfig[1] == 0:
     self.set_value(1,self.pulsecounter,False)
    elif self.taskdevicepluginconfig[1] == 1:
     self.set_value(1,self.pulsecounter,False)
     self.set_value(2,self.pulsetotalcounter,False)
     self.set_value(3,self.pulsetime,False)
    elif self.taskdevicepluginconfig[1] == 2:
     self.set_value(1,self.pulsetotalcounter,False)
    elif self.taskdevicepluginconfig[1] == 3:
     self.set_value(1,self.pulsecounter,False)
     self.set_value(2,self.pulsetotalcounter,False)
    self.plugin_senddata()
    self._lastdataservetime = rpieTime.millis()
    self.pulsecounter = 0
    result = True
  return result

 def p003_handler(self,channel):
  if (self.irqinprogress == False):
   self.irqinprogress = True
   atime = rpieTime.millis()
   ptime = atime - self.pulsetimeprevious
   aval = gpios.HWPorts.input(channel)
   if (ptime > int(self.taskdevicepluginconfig[0])):
    ok = False
    if self.taskdevicepluginconfig[2] == gpios.BOTH:
     ok = True
    elif self.taskdevicepluginconfig[2] == gpios.RISING:
     if self.prevval<aval:
      ok = True
    elif self.taskdevicepluginconfig[2] == gpios.FALLING:
     if self.prevval>aval:
      ok = True
    if ok:
     self.pulsecounter += 1
     self.pulsetotalcounter += 1
     self.pulsetime = ptime
     self.pulsetimeprevious = atime
    self.prevval = aval
   self.irqinprogress = False
