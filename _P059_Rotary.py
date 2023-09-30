#!/usr/bin/env python3
#############################################################################
#################### Rotary encoder plugin for RPIEasy ######################
#############################################################################
#
# Can only be used with devices that supports GPIO operations!
#
# Also be sure to set up pin using mode at Hardware->Pinout&Ports menu. (INPUT-PULLUP)
#
# Based on:
#  https://github.com/modmypi/Rotary-Encoder
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# Hardware device for this plugin implementation and testing provided by happytm.
# This plugin would never have been created without happytm! :)
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import webserver

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 59
 PLUGIN_NAME = "Input - Rotary Encoder (TESTING)"
 PLUGIN_VALUENAME1 = "Counter"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = False
  self.timeroptional = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.clklast = -1
  self.timer100ms = False

 def plugin_exit(self):
  if self.enabled and self.timer100ms==False:
   try:
    gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
   except:
    pass
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  try:
   if float(self.uservar[0])<int(self.taskdevicepluginconfig[1]): # minvalue check
    self.set_value(1,self.taskdevicepluginconfig[1],False)
   if float(self.uservar[0])>int(self.taskdevicepluginconfig[2]): # maxvalue check
    self.set_value(1,self.taskdevicepluginconfig[2],False)
  except:
    self.set_value(1,self.taskdevicepluginconfig[1],False)
  if int(self.taskdevicepin[0])>=0 and self.enabled and int(self.taskdevicepin[1])>=0:
   try:
    gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
   except:
    pass
   try:
    btime = int(self.taskdevicepluginconfig[3])
    if btime<0:
     btime = 0
   except:
    btime = 10
   try:
    self.clklast = gpios.HWPorts.input(int(self.taskdevicepin[0]))
    gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.FALLING,self.p059_handler,btime)
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Event can not be added")
    self.initialized = False
  else:
   self.initialized = False

 def webform_load(self): # create html page for settings
  webserver.addFormNote("1st GPIO=CLK, 2nd GPIO=DT, BOTH of them needs to be INPUT-PULLUP")
  choice1 = int(float(self.taskdevicepluginconfig[0]))
  options = ["1","2","3","4"]
  optionvalues = [1,2,3,4]
  webserver.addFormSelector("Step","p059_step",len(options),options,optionvalues,None,choice1)
  try:
   minv = int(self.taskdevicepluginconfig[1])
  except:
   minv = 0
  webserver.addFormNumericBox("Limit min.","p059_min",minv,-65535,65535)
  try:
   maxv = int(self.taskdevicepluginconfig[2])
  except:
   maxv = 100
  if minv>=maxv:
   maxv = minv+1
  webserver.addFormNumericBox("Limit max.","p059_max",maxv,-65535,65535)
  try:
   bt = int(self.taskdevicepluginconfig[3])
  except:
   bt = 10
  webserver.addFormNumericBox("GPIO bounce time","p059_bounce",bt,0,1000)
  webserver.addUnit("ms")
  return True

 def webform_save(self,params): # process settings post reply
  changed = False
  par = webserver.arg("p059_step",params)
  if par == "":
    par = 1
  if str(self.taskdevicepluginconfig[0]) != str(par):
   changed = True
  try:
   self.taskdevicepluginconfig[0] = int(par)
  except:
   self.taskdevicepluginconfig[0] = 1
  par = webserver.arg("p059_min",params)
  if par == "":
    par = 0
  if str(self.taskdevicepluginconfig[1]) != str(par):
   changed = True
  try:
   self.taskdevicepluginconfig[1] = int(par)
  except:
   self.taskdevicepluginconfig[1] = 0
  par = webserver.arg("p059_max",params)
  if par == "":
    par = 100
  if int(self.taskdevicepluginconfig[1])>=int(par):
    par = int(self.taskdevicepluginconfig[1])+1
  if str(self.taskdevicepluginconfig[2]) != str(par):
   changed = True
  try:
   self.taskdevicepluginconfig[2] = int(par)
  except:
   self.taskdevicepluginconfig[2] = 100

  par = webserver.arg("p059_bounce",params)
  try:
   if par == "":
    par = 10
   else:
    par = int(par)
  except:
   par = 10
  if par != int(self.taskdevicepluginconfig[3]):
   changed = True
   self.taskdevicepluginconfig[3] = par

  if changed:
   self.plugin_init()
  return True

 def p059_handler(self,channel):
  if self.initialized and self.enabled:
   aclk = gpios.HWPorts.input(self.taskdevicepin[0])
   if aclk != self.clklast:
    dtstate = gpios.HWPorts.input(self.taskdevicepin[1])
    try:
     ac = float(self.uservar[0])
    except:
     ac = 0
    if dtstate !=  aclk:
     if ac<int(self.taskdevicepluginconfig[2]):
      ac += int(self.taskdevicepluginconfig[0])
    else:
     if ac>int(self.taskdevicepluginconfig[1]):
      ac -= int(self.taskdevicepluginconfig[0])
    self.clklast = aclk
    self.set_value(1,ac,True)
    self._lastdataservetime = rpieTime.millis()
#    time.sleep(0.01)
