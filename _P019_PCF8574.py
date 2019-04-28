#!/usr/bin/env python3
#############################################################################
################ PCF8574 port extender plugin for RPIEasy ###################
#############################################################################
#
#
# Available commands:
#  PCFGPIO,<pin>,<state>		 - digital GPIO output, state can be: 0/1
#  PCFPULSE,<pin>,<state>,<duration>	 - state can be 0/1, set gpio to <state> then after <duration> milliseconds reverses it's state
#  PCFLONGPULSE,<pin>,<state>,<duration> - state can be 0/1, set gpio to <state> then after <duration> seconds reverses it's state
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
import lib.lib_pcfrouter as lib_pcfrouter

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 19
 PLUGIN_NAME = "Extra IO - PCF8574"
 PLUGIN_VALUENAME1 = "State"

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
  self.inverselogicoption = True
  self.recdataoption = True
  self.pcf = None
  self.i2ca = 0
  self.rpin = -1
  self.i2cport = -1
  self.timer100ms = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  self.initialized = False
  if self.enabled:
   i2cport = -1
   try:
    for i in range(0,2):
     if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
      i2cport = i
      break
   except:
    i2cport = -1
   if i2cport>-1:
     try:
      pinnum = int(self.taskdevicepluginconfig[0])
     except:
      pinnum = 0
     try:
      i2ca, self.rpin = lib_pcfrouter.get_pcf_pin_address(pinnum)
      self.pcf = lib_pcfrouter.request_pcf_device(pinnum)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCF device requesting failed: "+str(e))
      self.pcf = None
   if self.pcf is None or self.pcf.initialized==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCF can not be initialized! ")
   else:
    self.initialized = True
    intok = False
    try:
     self.uservar[0] = self.pcf.readpin(self.rpin)
     if int(self.taskdevicepin[0])>0:
      self.pcf.setexternalint(int(self.taskdevicepin[0]))
      self.pcf.setcallback(self.rpin,self.p019_handler)
      intok = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCF interrupt configuration failed:"+str(e))
     intok = False
    if intok:
     self.timer100ms = False
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCF 1/10s timer disabled")
    elif int(self.interval)==0: # if no interval setted and not interrupt selected setup a failsafe method
     self.timer100ms = True
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCF 1/10s timer enabled")
    try:
     self.ports = str(self.taskdevicepluginconfig[0])
    except:
     self.ports = 0
  else:
   self.ports = 0
   self.timer100ms = False
   self.pcf.setcallback(self.rpin,None)

 def plugin_exit(self):
    try:
     if self.rpin>-1:
      self.pcf.setcallback(self.rpin,None)
    except:
     pass
    plugin.PluginProto.plugin_exit(self)

 def webform_load(self): # create html page for settings
  try:
   if self.pcf.externalintsetted:
    self.taskdevicepin[0]=self.pcf.extinta
  except Exception as e:
   pass
  webserver.addFormPinSelect("PCF interrupt","taskdevicepin0",self.taskdevicepin[0])
  webserver.addFormNote("Add one RPI INPUT-PULLUP pin to handle input changes immediately - not needed for interval input reading and output using")
  webserver.addFormNumericBox("Port","p019_pnum",self.taskdevicepluginconfig[0],1,128)
  webserver.addFormNote("First extender 1-8 (0x20), Second 9-16 (0x21)...")
  return True

 def webform_save(self,params): # process settings post reply
   p1 = self.taskdevicepin[0]
   p2 = self.taskdevicepluginconfig[0]
   par = webserver.arg("p019_pnum",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
   except:
    self.taskdevicepluginconfig[0] = 0
   try:
    self.taskdevicepin[0]=webserver.arg("taskdevicepin0",params)
   except:
    self.taskdevicepin[0]=-1
   if p1!=self.taskdevicepin[0] or p2!=self.taskdevicepluginconfig[0]:
    self.plugin_init()
   return True

 def p019_handler(self,pin,val):
  if pin==self.rpin:
   try:
    if float(val)!=float(self.uservar[0]):
     self.set_value(1,val,True)
     self._lastdataservetime = rpieTime.millis()
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))

 def timer_ten_per_second(self):
  if self.initialized and self.enabled:
   try:
    val = self.pcf.readpin(self.rpin)
    if int(val) != int(float(self.uservar[0])):
     self.set_value(1,val,True)
     self._lastdataservetime = rpieTime.millis()
   except:
    pass
  return self.timer100ms

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled and self.readinprogress==0:
    self.readinprogress = 1
    try:
     result = self.pcf.readpin(self.rpin)
     self.set_value(1,result,True)
     self._lastdataservetime = rpieTime.millis()
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.readinprogress = 0
    result = True
  return result

 def plugin_write(self,cmd): # handle incoming commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "pcfgpio":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    ti2ca, trpin = lib_pcfrouter.get_pcf_pin_address(pin)
    val = int(cmdarr[2].strip())
   except:
    pin = -1
    trpin = -1
   if pin>-1 and val in [0,1] and trpin >-1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCFPIO"+str(pin)+" set to "+str(val))
    try:
     tmcp = lib_pcfrouter.request_pcf_device(int(pin))
     tmcp.writepin(trpin, val)
     res = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCFGPIO"+str(pin)+": "+str(e))
   return res
  elif cmdarr[0]=="pcfpulse":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    ti2ca, trpin = lib_pcfrouter.get_pcf_pin_address(pin)
    val = int(cmdarr[2].strip())
   except:
    pin = -1
    trpin = -1
   dur = 100
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 100
   if pin>-1 and val in [0,1] and trpin >-1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCFGPIO"+str(pin)+": Pulse started")
    try:
     tmcp = lib_pcfrouter.request_pcf_device(int(pin))
     tmcp.writepin(trpin, val)
     s = float(dur/1000)
     time.sleep(s)
     tmcp.writepin(trpin, (1-val))
     res = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCFGPIO"+str(pin)+": "+str(e))
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCFGPIO"+str(pin)+": Pulse ended")
   return res
  elif cmdarr[0]=="pcflongpulse":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    ti2ca, trpin = lib_pcfrouter.get_pcf_pin_address(pin)
    val = int(cmdarr[2].strip())
   except:
    pin = -1
    trpin = -1
   dur = 2
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 2
   if pin>-1 and val in [0,1] and trpin >-1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCFGPIO"+str(pin)+": LongPulse started")
    try:
     tmcp = lib_pcfrouter.request_pcf_device(int(pin))
     tmcp.writepin(trpin, val)
     res = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCFGPIO"+str(pin)+": "+str(e))
    rarr = [int(pin),(1-val)]
    rpieTime.addsystemtimer(dur,self.p019_timercb,rarr)
  return res

 def p019_timercb(self,stimerid,ioarray):
  if ioarray[0] > -1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCFGPIO"+str(ioarray[0])+": LongPulse ended")
    try:
     tmcp = lib_pcfrouter.request_pcf_device(int(ioarray[0]))
     ti2ca, trpin = lib_pcfrouter.get_pcf_pin_address(int(ioarray[0]))
     tmcp.writepin(trpin, int(ioarray[1]))
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCFGPIO"+str(ioarray[0])+": "+str(e))

