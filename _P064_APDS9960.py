#!/usr/bin/env python3
#############################################################################
####################### APDS9960 plugin for RPIEasy #########################
#############################################################################
#
# Can report gesture OR light+proximity but not both at the same time.
# Reports gestures as DIMMER values - Selector Switch at Domoticz
#  0:None, 10:Left, 20: Right, 30: Up, 40: Down, 50: Near, 60: Far
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
from apds9960.const import *
from apds9960 import APDS9960
import gpios
import smbus

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 64
 PLUGIN_NAME = "Input - APDS9960 Gesture sensor"
 PLUGIN_VALUENAME1 = "Gesture"   # Switch Levels: 0:None, 10:Left, 20: Right, 30: Up, 40: Down, 50: Near, 60: Far
 PLUGIN_VALUENAME2 = "Proximity" # in between 70-200mm (<70 is zero)
 PLUGIN_VALUENAME3 = "Light"     # ambient light level, lux?
 ADDR = 0x39
 # gesture and other functions will not work at the same time

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.apds = None
  self.timer100ms = True
  self.readinprogress = False

 def __del__(self):
   if self.taskdevicepin[0]>=0 and self.enabled:
    try:
     gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
    except:
     pass

 def plugin_exit(self):
  self.__del__()
  return True

 def plugin_init(self,enableplugin=None):
  initok = False
  self.readinprogress = False
  if self.enabled:
   if self.taskdevicepin[0]>=0:
    try:
     gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.FALLING,self.p064_handler,200)
     self.timer100ms = False
    except Exception as e:
     if str(self.taskdevicepluginconfig[0])=="0":
      self.timer100ms = True
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Interrupt error "+str(e)) 
   else:
    if str(self.taskdevicepluginconfig[0])=="0":
     self.timer100ms = True

   try:
     i2cok = gpios.HWPorts.i2c_init()
     if i2cok:
      if self.interval>2:
       nextr = self.interval-2
      else:
       nextr = self.interval
      self.apds = APDS9960(gpios.HWPorts.i2cbus)
      self._lastdataservetime = rpieTime.millis()-(nextr*1000)
      self.lastread = 0
      initok = True
     else:
      self.enabled = False
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"I2C can not be initialized!") 
   except Exception as e:
     self.enabled = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"APDS init error "+str(e))
  if initok:
   try:
    self.apds.setProximityIntLowThreshold(50)
    if str(self.taskdevicepluginconfig[0])=="1":
     self.apds.enableProximitySensor()
     self.apds.enableLightSensor()
    else:
     self.apds.enableGestureSensor()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"APDS setup error "+str(e))
   plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = initok

 def webform_load(self): # create html page for settings
  webserver.addFormNote("I2C address is fixed 0x39! You can check it at <a href='i2cscanner'>i2cscan</a> page.")
  webserver.addFormPinSelect("Interrupt pin","p064_int_pin",self.taskdevicepin[0])
  webserver.addFormNote("Set an Input for using interrupt pin or none if you want to scan gestures continously!")
  choice1 = self.taskdevicepluginconfig[0]
  options = ["Gesture/Dimmer","Proximity+Light/Dual"]
  optionvalues = [0,1]
  webserver.addFormSelector("Type","p064_type",2,options,optionvalues,None,choice1)
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p064_int_pin",params)
   if par == "":
    par = -1
   self.taskdevicepin[0] = int(par)
   par = webserver.arg("p064_type",params)
   if par == "":
    par = -1
   self.taskdevicepluginconfig[0] = int(par)
   if int(par)==1:
    self.set_valuenames(self.PLUGIN_VALUENAME2,self.PLUGIN_VALUENAME3)
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
   else:
    self.set_valuenames(self.PLUGIN_VALUENAME1)
    self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
   try:
    if self.taskdevicepin[0]>=0:
     gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
   except:
    pass
   self.set_value(1,0,False)
   self.set_value(2,0,False)
   self.initialized = False
   self.plugin_init()
   return True

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled:
   if str(self.taskdevicepluginconfig[0])=="1":
    try:
     prox = self.apds.readProximity()
     prox = int((255-prox)*0.78) # convert to mm
     if prox < 0:
      prox = 0
     elif prox>200:
      prox = 200
     if prox != self.uservar[0]: 
      self.set_value(1,(prox),False)
     val = self.apds.readAmbientLight()
     if val != self.uservar[1]:
      self.set_value(2,(val),False)
    except Exception as e:
     self.set_value(1,0,False)
     self.set_value(2,0,False)
   else:
    self.uservar[0] = 0
    self.p064_get_gesture()
   self.plugin_senddata()
   rpieTime.addsystemtimer(2,self.p064_timercb,[-1])
   self._lastdataservetime = rpieTime.millis()
   result = True
  return result

 def timer_ten_per_second(self): # called 10 times per second (best effort)
  if self.initialized and self.enabled:
   tvar = self.uservar[0]
   self.p064_get_gesture()
   if int(tvar) != int(self.uservar[0]): # publish changes if different gesture received than previous
    self.plugin_senddata()
    rpieTime.addsystemtimer(3,self.p064_timercb,[-1]) # reset gesture to None (0) after 3 sec
  return True

 def p064_handler(self,channel): # this function called when interrupt pin pulled low
  self.p064_get_gesture()
  self.plugin_senddata()
  rpieTime.addsystemtimer(3,self.p064_timercb,[-1]) # reset gesture to None (0) after 3 sec
  self._lastdataservetime = rpieTime.millis()

 def p064_get_gesture(self):
  if self.readinprogress==False:
   self.readinprogress = True
   try:
    if self.apds.isGestureAvailable():
     motion = self.apds.readGesture()
     self.set_value(1,(motion*10),False) # Switch Levels: 0:None, 10:Left, 20: Right, 30: Up, 40: Down, 50: Near, 60: Far
   except Exception as e:
    pass # no error handling here, this function can be called very frequently
   self.readinprogress = False

 def p064_timercb(self,stimerid):
  self.uservar[0] = 0
