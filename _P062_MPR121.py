#!/usr/bin/env python3
#############################################################################
###################### MPR121 keypad plugin for RPIEasy #####################
#############################################################################
#
# Based on:
#  https://github.com/williamhbell/MPR121CapSensor
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time
import lib.lib_mprrouter as mprrouter

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 62
 PLUGIN_NAME = "Keypad - MPR121 Touch (TESTING)"
 PLUGIN_VALUENAME1 = "ScanCode"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.ports = 0
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.mpr = None
  self.timer100ms = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  self.initialized = False
  self.timer100ms = False
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
      i2ca = int(self.taskdevicepluginconfig[0])
     except:
      i2ca = 0
     try:
      intpin = int(self.taskdevicepin[0])
     except:
      intpin = -1
     if i2ca>0:
      try:
       self.mpr = mprrouter.request_mpr_device(i2cl, i2ca)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MPR device requesting failed: "+str(e))
       self.mpr = None
     else:
       self.mpr = None
   if self.mpr is not None:
    self.initialized = True
    self.uservar[0] = 0
    if intpin>=0:
     try:
      self.__del__()
      gpios.HWPorts.add_event_detect(intpin, gpios.FALLING, self.p062_handler)
     except:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MPR interrupt setting failed: "+str(e))
     self.timer100ms = False
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MPR 1/10s timer disabled")
    elif int(self.interval)==0: # if no interval setted and not interrupt selected setup a failsafe method
     self.timer100ms = True
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MPR 1/10s timer enabled")
  else:
   self.timer100ms = False

 def webform_load(self): # create html page for settings
  webserver.addFormPinSelect("MPR interrupt","taskdevicepin0",self.taskdevicepin[0])
  webserver.addFormNote("Add one RPI INPUT-PULLUP pin to handle input changes immediately - not needed for interval input reading and output using")
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x5a","0x5b","0x5c","0x5d"]
  optionvalues = [0x5a,0x5b,0x5c,0x5d]
  webserver.addFormSelector("I2C address","p062_addr",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  webserver.addFormCheckBox("ScanCode","scancode",self.taskdevicepluginconfig[1])
  return True

 def webform_save(self,params): # process settings post reply
   sc = (webserver.arg("scancode",params)=="on")
   self.taskdevicepluginconfig[1] = sc
   p1 = self.taskdevicepin[0]
   p2 = self.taskdevicepluginconfig[0]
   par = webserver.arg("p062_addr",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
   except:
    self.taskdevicepluginconfig[0] = 0
   try:
    self.taskdevicepin[0]=webserver.arg("taskdevicepin0",params)
   except:
    self.taskdevicepin[0]=-1
   if int(p1)!=int(self.taskdevicepin[0]) or int(p2)!=int(self.taskdevicepluginconfig[0]):
    self.plugin_init()
   return True

 def p062_handler(self,pin):
  if self.initialized and self.enabled and self.readinprogress==0:
   try:
    self.readinprogress = 1
    key = self.mpr.readTouch()
    if key>0:
     if self.taskdevicepluginconfig[1]==False:
      key=self.mpr.get_key_map(key)
     self.set_value(1,key,True)
     self._lastdataservetime = rpieTime.millis()
   except Exception as e:
    pass
   self.readinprogress = 0

 def timer_ten_per_second(self):
  self.p062_handler(0)
  return self.timer100ms

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled and self.readinprogress==0:
    self.readinprogress = 1
    self.p062_handler(0)
    self.readinprogress = 0
    result = True
  return result

 def __del__(self):
  if self.enabled:
   try:
    gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
   except:
    pass

 def plugin_exit(self):
   self.__del__()
