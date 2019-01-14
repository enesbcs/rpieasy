#!/usr/bin/env python3
#############################################################################
####################### Dual Switch plugin for RPIEasy ######################
#############################################################################
#
# Made for supporting combined PIR/MW motion sensor.
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
  except: 
   pass
  try:
   if self.initialized:
    gpios.HWPorts.remove_event_detect(self.taskdevicepin[1])
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
  if self.taskdevicepin[0]<0 or self.taskdevicepin[1]<0:
   self.enabled=False
   self.initialized=False
  if self.enabled:
   self.__del__()
   try:
    gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.BOTH,self.p200_handler,200)
    gpios.HWPorts.add_event_detect(self.taskdevicepin[1],gpios.BOTH,self.p200_handler,200)
    self.timer100ms = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"GPIO event handlers can not be created "+str(e))
    self.__del__()
    self.timer100ms = True
   self.laststate = 0
   if self.initialized:
    self.laststate = -1
    self.p200_handler(self.taskdevicepin[0]) # get state

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled:
   self.timer_ten_per_second()
   self.set_value(1,self.actualstate,True)
   self._lastdataservetime = rpieTime.millis()
   result = True
  return result

 def timer_ten_per_second(self):
  if self.initialized and self.enabled:
   v1 = gpios.HWPorts.input(self.taskdevicepin[0])
   v2 = gpios.HWPorts.input(self.taskdevicepin[1])
   if (v1==1) and (v2==1):
    self.actualstate = 1
   if (v1==0) and (v2==0):
    self.actualstate = 0
   if float(self.actualstate) != float(self.laststate):
    self.set_value(1,self.actualstate,True)
    self.laststate = self.actualstate
    self._lastdataservetime = rpieTime.millis()
   if int(self.uservar[1])!=int(v1):
    self.set_value(2,v1,False)
   if int(self.uservar[2])!=int(v2):
    self.set_value(3,v2,False)

 def p200_handler(self,channel):
  self.timer_ten_per_second()
