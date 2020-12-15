#!/usr/bin/env python3
#############################################################################
######################## Switch plugin for RPIEasy ##########################
#############################################################################
#
# Can only be used with devices that supports GPIO operations!
#
# Available commands: (It is evident, that you have to enable at least one P001 device if you want to use it's commands)
#  gpio,26,1           - set pin GPIO26 to 1 (HIGH)
#  pwm,18,50,100,20000 - set pin GPIO18 to PWM mode with 100msec fade and 20000Hz sample rate and 50% fill ratio
#                        PWM is software based if not one of the dedicated H-PWM pins
#                        H-PWM has to be set before use this command and may need root rights!
#  pulse,26,1,500      - set pin GPIO26 to 1 for 500 msec than set back to 0 (blocking mode)
#  longpulse,26,1,10   - set pin GPIO26 to 1 for 10 seconds than set back to 0 (non-blocking mode)
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
import lib.lib_gpiohelper as gpiohelper
import webserver
try:
 import gpios
 gpioinit = True
except:
 gpioinit = False

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

 def plugin_exit(self):
  if self.enabled and self.timer100ms==False:
   try:
    gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
   except:
    pass
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.decimals[1]=0
  self.decimals[2]=0
  self.initialized = False
  try:
   gpioinit = gpios.HWPorts is not None
  except:
   gpioinit = False
  if int(self.taskdevicepin[0])>=0 and self.enabled and gpioinit:
   try:
    self.set_value(1,int(gpios.HWPorts.input(int(self.taskdevicepin[0]))),True) # Sync plugin value with real pin state
   except:
    pass
   try:
    if int(self.taskdevicepluginconfig[3])<1:
     self.taskdevicepluginconfig[3] = gpios.BOTH # for compatibility
   except:
    self.taskdevicepluginconfig[3] = gpios.BOTH
   try:
    self.plugin_exit()
    if self.taskdevicepluginconfig[0]:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Registering 10/sec timer as asked")
     self.timer100ms = True
     self.initialized = True
     return True
    if int(self.taskdevicepluginconfig[1])>0:
     gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),int(self.taskdevicepluginconfig[3]),self.p001_handler,int(self.taskdevicepluginconfig[1]))
    else:
     gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),int(self.taskdevicepluginconfig[3]),self.p001_handler)
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Event registered to pin "+str(self.taskdevicepin[0]))
    self.timer100ms = False
    self._lastdataservetime = 0

    if self.taskdevicepluginconfig[4]>0:
     self.valuecount = 3
     self.uservar[1]=-1
     if len(self.valuenames)<3:
       self.valuenames.append("")
       self.valuenames.append("")
     if self.valuenames[1]=="":
      self.valuenames[1]="Longpress"
      self.valuenames[2]="PressedTime"
    else:
     self.valuecount = 1
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Event can not be added, register backup timer "+str(e))
    self.timer100ms = True
   self.initialized = True

 def webform_load(self):
  webserver.addFormNote("Please make sure to select <a href='pinout'>pin configured</a> for input for default (or output to report back its state)!")
  webserver.addFormCheckBox("Force 10/sec periodic checking of pin","p001_per",self.taskdevicepluginconfig[0])
  webserver.addFormNote("For output pin, only 10/sec periodic method will work!")
  webserver.addFormNumericBox("De-bounce (ms)","p001_debounce",self.taskdevicepluginconfig[1],0,1000)
  options = ["Normal Switch","Push Button Active Low","Push Button Active High"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Switch Button Type","p001_button",len(optionvalues),options,optionvalues,None,self.taskdevicepluginconfig[2])
  webserver.addFormNote("Use only normal switch for output type, i warned you!")
  try:
   options = ["BOTH","RISING","FALLING"]
   optionvalues = [gpios.BOTH,gpios.RISING,gpios.FALLING]
   webserver.addFormSelector("Event detection type","p001_det",len(optionvalues),options,optionvalues,None,self.taskdevicepluginconfig[3])
   webserver.addFormNote("Only valid if event detection activated")
  except:
   pass
  options = ["None","1-->0","0-->1","Both"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Longpress detection","p001_long",len(optionvalues),options,optionvalues,None,self.taskdevicepluginconfig[4])
  webserver.addFormNumericBox("Longpress min time (ms)","p001_longtime",self.taskdevicepluginconfig[5],0,10000)
  return True

 def webform_save(self,params):
  changed = False
  prevval = self.taskdevicepluginconfig[0]
  if (webserver.arg("p001_per",params)=="on"):
   self.taskdevicepluginconfig[0] = True
  else:
   self.taskdevicepluginconfig[0] = False
  if prevval != self.taskdevicepluginconfig[0]:
   changed = True

  prevval = self.taskdevicepluginconfig[1]
  par = webserver.arg("p001_debounce",params)
  try:
   self.taskdevicepluginconfig[1] = int(par)
  except:
   self.taskdevicepluginconfig[1] = 0
  if prevval != self.taskdevicepluginconfig[1]:
   changed = True

  prevval = self.taskdevicepluginconfig[2]
  par = webserver.arg("p001_button",params)
  try:
   self.taskdevicepluginconfig[2] = int(par)
  except:
   self.taskdevicepluginconfig[2] = 0
  if prevval != self.taskdevicepluginconfig[2]:
   changed = True

  prevval = self.taskdevicepluginconfig[3]
  par = webserver.arg("p001_det",params)
  try:
   self.taskdevicepluginconfig[3] = int(par)
  except:
   self.taskdevicepluginconfig[3] = gpios.BOTH
  if prevval != self.taskdevicepluginconfig[3]:
   changed = True

  prevval = self.taskdevicepluginconfig[4]
  par = webserver.arg("p001_long",params)
  try:
   self.taskdevicepluginconfig[4] = int(par)
  except:
   self.taskdevicepluginconfig[4] = 0
  if prevval != self.taskdevicepluginconfig[4]:
   changed = True

  par = webserver.arg("p001_longtime",params)
  try:
   self.taskdevicepluginconfig[5] = int(par)
  except:
   self.taskdevicepluginconfig[5] = 1000

  if changed:
   self.plugin_init()
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
    if self.taskdevicepluginconfig[4]>0 and self._lastdataservetime>0: # check for longpress
     docheck = False
     if self.taskdevicepluginconfig[4]==3:
      docheck = True
     elif self.taskdevicepluginconfig[4]==1 and int(prevval)==1 and int(outval)==0:
      docheck = True
     elif self.taskdevicepluginconfig[4]==2 and int(prevval)==0 and int(outval)==1:
      docheck = True
     self.set_value(1,int(outval),False)
     diff = (rpieTime.millis()-self._lastdataservetime)
     dolong = False
     if docheck:
       if diff > self.taskdevicepluginconfig[5]:
        dolong = True
     if dolong:
      self.set_value(2,1,False)
     else:
      self.set_value(2,0,False)
     if docheck:
      self.set_value(3,diff,False)
     else:
      self.set_value(3,0,False)
     self.plugin_senddata()
    else:
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
  if cmdarr[0].strip().lower() in gpiohelper.commandlist:
   res = gpiohelper.gpio_commands(cmd)
  return res

 def postchecker(self,timerid,pararray):
  if (pararray[0]==int(self.taskdevicepin[0])):
   self.timer_ten_per_second()
