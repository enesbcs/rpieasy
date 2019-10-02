#!/usr/bin/env python3
#############################################################################
######################## Switch plugin for RPIEasy ##########################
#############################################################################
#
# Can only be used with devices that supports GPIO operations!
#
# Available commands: (It is evident, that you have to enable at least one P001 device if you want to use it's commands)
#  gpio,26,1          - set pin GPIO26 to 1 (HIGH)
#  pwm,18,50,20000    - set pin GPIO18 to PWM mode with 20000Hz sample rate and 50% fill ratio
#                       PWM is software based if not one of the dedicated H-PWM pins
#                       H-PWM has to be set before use this command and may need root rights!
#  pulse,26,1,500     - set pin GPIO26 to 1 for 500 msec than set back to 0 (blocking mode)
#  longpulse,26,1,10  - set pin GPIO26 to 1 for 10 seconds than set back to 0 (non-blocking mode)
#
# Also be sure to set up pin using mode at Hardware->Pinout&Ports menu.
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import lib.lib_gpiohelper as gpiohelper
import webserver

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
    gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
   except:
    pass

 def plugin_exit(self):
  self.__del__()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  if int(self.taskdevicepin[0])>=0 and self.enabled:
   self.set_value(1,int(gpios.HWPorts.input(int(self.taskdevicepin[0]))),True) # Sync plugin value with real pin state
   try:
    self.__del__()
    if self.taskdevicepluginconfig[0]:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Registering 10/sec timer as asked")
     self.timer100ms = True
     return True
    if int(self.taskdevicepluginconfig[1])>0:
     gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),gpios.BOTH,self.p001_handler,int(self.taskdevicepluginconfig[1]))
    else:
     gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),gpios.BOTH,self.p001_handler)
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Event registered to pin "+str(self.taskdevicepin[0]))
    self.timer100ms = False
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Event can not be added, register backup timer")
    self.timer100ms = True

 def webform_load(self):
  webserver.addFormNote("Please make sure to select <a href='pinout'>pin configured</a> for input for default (or output to report back its state)!")
  webserver.addFormCheckBox("Force 10/sec periodic checking of pin","p001_per",self.taskdevicepluginconfig[0])
  webserver.addFormNote("For output pin, only 10/sec periodic method will work!")
  webserver.addFormNumericBox("De-bounce (ms)","p001_debounce",self.taskdevicepluginconfig[1],0,1000)
  options = ["Normal Switch","Push Button Active Low","Push Button Active High"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Switch Button Type","p001_button",len(optionvalues),options,optionvalues,None,self.taskdevicepluginconfig[2])
  webserver.addFormNote("Use only normal switch for output type, i warned you!")
  return True

 def webform_save(self,params):
  if (webserver.arg("p001_per",params)=="on"):
   self.taskdevicepluginconfig[0] = True
  else:
   self.taskdevicepluginconfig[0] = False
  par = webserver.arg("p001_debounce",params)
  try:
   self.taskdevicepluginconfig[1] = int(par)
  except:
   self.taskdevicepluginconfig[1] = 0
  par = webserver.arg("p001_button",params)
  try:
   self.taskdevicepluginconfig[2] = int(par)
  except:
   self.taskdevicepluginconfig[2] = 0
  return True

 def plugin_read(self):
  result = False
  if self.initialized:
   self.set_value(1,int(float(self.uservar[0])),True)
   self._lastdataservetime = rpieTime.millis()
   result = True
  return result

 def p001_handler(self,channel):
  self.pinstate_check(True)

 def timer_ten_per_second(self):
  self.pinstate_check()

 def pinstate_check(self,postcheck=False):
  if self.initialized and self.enabled:
   prevval = int(float(self.uservar[0]))
   inval = gpios.HWPorts.input(int(self.taskdevicepin[0]))
   if self.pininversed:
    prevval=1-int(prevval)
   outval = prevval
   if int(self.taskdevicepluginconfig[2])==0: # normal switch
    outval = int(inval)
   elif int(self.taskdevicepluginconfig[2])==1: # active low button
    if inval==0:             # if low
     outval = 1-int(prevval) # negate
   elif int(self.taskdevicepluginconfig[2])==2: # active high button
    if inval==1:             # if high
     outval = 1-int(prevval) # negate
   if prevval != outval:
    self.set_value(1,int(outval),True)
    self._lastdataservetime = rpieTime.millis()
    if self.taskdevicepluginconfig[2]>0 and self.timer100ms:
      time.sleep(self.taskdevicepluginconfig[1]/1000) # force debounce if not event driven detection
    if postcheck:
     rpieTime.addsystemtimer(1,self.postchecker,[int(self.taskdevicepin[0]),int(float(self.uservar[0]))]) # failsafe check

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0].strip().lower() in ["gpio","pwm","pulse","longpulse","tone","rtttl"]:
   res = gpiohelper.gpio_commands(cmd)
  return res

 def postchecker(self,timerid,pararray):
  if (pararray[0]==int(self.taskdevicepin[0])):
   self.timer_ten_per_second()
