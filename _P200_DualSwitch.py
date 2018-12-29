#!/usr/bin/env python3
#############################################################################
####################### Dual Switch plugin for RPIEasy ######################
#############################################################################
#
# Made for supporting combined PIR/MW motions sensor.
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 200
 PLUGIN_NAME = "Input - Dual Switch Device"
 PLUGIN_VALUENAME1 = "State"
 PLUGIN_VALUENAME2 = "State1"
 PLUGIN_VALUENAME3 = "State2"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 3
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = True
  self.recdataoption = False
  self.laststate = 0
  self.actualstate = 0

 def __del__(self):
  try:
   if self.initialized:
    gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
    gpios.HWPorts.remove_event_detect(self.taskdevicepin[1])
  except: 
   pass

 def plugin_exit(self):
  self.__del__()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.taskdevicepin[0]<0 or self.taskdevicepin[1]<0:
   self.enabled=False
   self.initialized=False
  if self.enabled:
   try:
    gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.BOTH,self.p001_handler,200)
    gpios.HWPorts.add_event_detect(self.taskdevicepin[1],gpios.BOTH,self.p001_handler,200)
   except Exception as e:
    self.initialized = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"GPIO event handlers can not be created "+str(e))
   self.laststate = 0
   if self.initialized:
    self.laststate = -1
    self.p001_handler(self.taskdevicepin[0])

 def plugin_read(self):
  result = False
  if self.initialized:
   self.set_value(1,self.actualstate,True)
   self._lastdataservetime = rpieTime.millis()
   result = True
  return result
 
 def p001_handler(self,channel):
  if self.initialized:
   v1 = gpios.HWPorts.input(self.taskdevicepin[0])
   v2 = gpios.HWPorts.input(self.taskdevicepin[1])
   if (v1==1) and (v2==1):
    self.actualstate = 1
   if (v1==0) and (v2==0):
    self.actualstate = 0
   if self.actualstate != self.laststate:
    self.set_value(1,self.actualstate,True)
    self.laststate = self.actualstate
    self._lastdataservetime = rpieTime.millis()
   if int(self.uservar[1])!=int(v1):
    self.set_value(2,v1,False)
   if int(self.uservar[2])!=int(v2):
    self.set_value(3,v2,False)
