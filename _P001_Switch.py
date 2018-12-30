#!/usr/bin/env python3
#############################################################################
######################## Switch plugin for RPIEasy ##########################
#############################################################################
#
# Can only be used with devices that supports GPIO operations!
#
# Available commands:
#  gpio,26,1          - set pin GPIO26 to 1 (HIGH)
#  pwm,18,50,20000    - set pin GPIO18 to PWM mode with 20000Hz sample rate and 50% fill ratio
#                       PWM is software based if not one of the dedicated H-PWM pins
#                       H-PWM has to be set before use this command and may need root rights!
#  pulse,26,1,500     - set pin GPIO26 to 1 for 500 msec than set back to 0 (blocking mode)
#  longpulse,26,1,10  - set pin GPIO26 to 1 for 10 seconds than set back to 0 (non-blocking mode)
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
 PLUGIN_ID = 1
 PLUGIN_NAME = "Input - Switch Device/Generic GPIO"
 PLUGIN_VALUENAME1 = "State"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SINGLE
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = True
  self.recdataoption = False

 def __del__(self):
  if self.enabled and self.timer100ms==False:
   try:
    gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
   except:
    pass

 def plugin_exit(self):
  self.__del__()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if int(self.taskdevicepin[0])>=0 and self.enabled:
   self.set_value(1,gpios.HWPorts.input(int(self.taskdevicepin[0])),True) # Sync plugin value with real pin state
   try:
    self.__del__()
    gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.BOTH,self.p001_handler,200)
    self.timer100ms = False
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Event can not be added, register backup timer")
    self.timer100ms = True

 def plugin_read(self):
  result = False
  if self.initialized:
   self.set_value(1,gpios.HWPorts.input(int(self.taskdevicepin[0])),True)
   self._lastdataservetime = rpieTime.millis()
   result = True
  return result
 
 def p001_handler(self,channel):
  self.timer_ten_per_second()

 def timer_ten_per_second(self):
  if self.initialized and self.enabled:
   val = gpios.HWPorts.input(int(self.taskdevicepin[0]))
   if int(val) != int(self.uservar[0]):
    self.set_value(1,val,True)
    self._lastdataservetime = rpieTime.millis()

 def p001_timercb(self,stimerid,ioarray):
  if ioarray[0] > -1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(ioarray[0])+": LongPulse ended")
    try:
     gpios.HWPorts.output(ioarray[0],ioarray[1])
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(ioarray[0])+": "+str(e))
 
 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "gpio":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   if pin>-1 and val in [0,1]:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(pin)+" set to "+str(val))
    suc = False
    try:
     suc = True
     gpios.HWPorts.output(pin,val)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+": "+str(e))
     suc = False
#    if suc == False:
#     try:
#      gpios.HWPorts.output(pin,val,True) # force output?
#     except Exception as e:
#      print("output failed ",pin,val,e)
#     suc = False
   res = True
  elif cmdarr[0]=="pwm":
   pin = -1
   prop = -1
   try:
    pin = int(cmdarr[1].strip())
    prop = int(cmdarr[2].strip())
   except:
    pin = -1
    prop = -1
   freq = 1000
   try:
    freq = int(cmdarr[3].strip())
   except:
    freq = 1000
   if pin>-1 and prop>-1:
    suc = False
    try:
     suc = True
     gpios.HWPorts.output_pwm(pin,prop,freq)
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(pin)+" PWM "+str(prop)+"% "+str(freq)+"Hz")
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+" PWM "+str(e))
     suc = False
   res = True
  elif cmdarr[0]=="pulse":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   dur = 100
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 100
   if pin>-1 and val in [0,1]:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(pin)+": Pulse started")
    try:
     gpios.HWPorts.output(pin,val)
     s = (dur/1000)
     time.sleep(s)
     gpios.HWPorts.output(pin,(1-val))
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+": "+str(e))
     suc = False
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(pin)+": Pulse ended")
   res = True
  elif cmdarr[0]=="longpulse":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   dur = 2
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 2
   if pin>-1 and val in [0,1]:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(pin)+": LongPulse started")
    try:
     gpios.HWPorts.output(pin,val)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+": "+str(e))
     suc = False
    rarr = [pin,(1-val)]
    rpieTime.addsystemtimer(dur,self.p001_timercb,rarr)
   res = True
  return res
