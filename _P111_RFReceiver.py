#!/usr/bin/env python3
#############################################################################
################## 433Mhz RF Receiver plugin for RPIEasy ####################
#############################################################################
#
# This plugin made for simple one GPIO based RF receivers.
#
# RF433 receiver plugin based on rc-switch:
#  https://github.com/sui77/rc-switch
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
from lib.lib_rcswitch import *

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 111
 PLUGIN_NAME = "Communication - RF433 Receiver (TESTING)"
 PLUGIN_VALUENAME1 = "Data"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SINGLE
   self.vtype = rpieGlobals.SENSOR_TYPE_LONG
   self.readinprogress = 0
   self.valuecount = 1
   self.senddataoption = True
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.rfdevice = None
   self.timer100ms = False

 def __del__(self):
  try:
   self.initialized = False
   self.timer100ms = False
   if self.rfdevice is not None:
    self.rfdevice.disableReceive()
  except:
   pass

 def plugin_exit(self):
  self.__del__()

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.set_value(1,"0",False)
  self.rfconnect()
#  if self.initialized == False:
#     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RF433 init failed")

 def rfconnect(self):
   if int(self.taskdevicepin[0])>=0 and self.enabled:
    try:
      self.rfdevice = getRFDev(True)
      pval = self.rfdevice.initpin()
      if self.rfdevice and int(pval)>0:
       self.initialized = True
       self.rfdevice.setReceiveTolerance(int(self.taskdevicepluginconfig[0]))
       self.rfdevice.enableReceive(int(self.taskdevicepin[0]))
       self.timer100ms = True
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RF433: "+str(e))
      self.initialized = False
      self.timer100ms = False
   else:
#      print("Not yet initialized")
      self.initialized = False
      self.timer100ms = False

 def webform_load(self):
   webserver.addFormNote("Select an input pin.")
   tol = self.taskdevicepluginconfig[0]
   try:
    tol = int(tol)
   except:
    tol = 0
   if tol == 0:
    tol = 60
   webserver.addFormNumericBox("Signal decoding tolerance","p111_tolerance",tol,1,200)
   webserver.addUnit("%")
   return True

 def webform_save(self,params):
  par = webserver.arg("p111_tolerance",params)
  if par == "":
   par = 0
  if par == 0:
   par = 60
  self.taskdevicepluginconfig[0] = int(par)
  self.rfconnect()
  return True

 def timer_ten_per_second(self):
   try:
       if self.rfdevice.available():
        rstr = self.rfdevice.getReceivedValue()
        self.rfdevice.resetAvailable()
        if rstr != 0:
         self.set_value(1,str(rstr),True)
   except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RF433: "+str(e))
