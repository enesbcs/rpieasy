#!/usr/bin/env python3
#############################################################################
################# (Domoticz) PWM helper for RPIEasy #########################
#############################################################################
#
# Only receiver! Communication is implemented through plugin_receivedata()
# Primarily for Domoticz, but can be used any MQTT based controllers.
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import lib.lib_gpiohelper as gpiohelper
import Settings

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 213
 PLUGIN_NAME = "Output - PWM Helper"
 PLUGIN_VALUENAME1 = "Value"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SINGLE
  self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.pullupoption = False
  self.inverselogicoption = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.sync()

 def webform_load(self):
  webserver.addFormNote("Please make sure to select <a href='pinout'>pin configured for Output or HPWM!</a>")
  webserver.addFormCheckBox("Preserve state at startup","p213_preserve",self.taskdevicepluginconfig[0])
  webserver.addFormCheckBox("Response to remote commands for non-Domoticz controllers","p213_report",self.taskdevicepluginconfig[1])
  webserver.addFormNumericBox("Frequency","p213_freq",self.taskdevicepluginconfig[2],0,19200000)
  return True

 def webform_save(self,params):
  if (webserver.arg("p213_preserve",params)=="on"):
   self.taskdevicepluginconfig[0] = True
  else:
   self.taskdevicepluginconfig[0] = False
  if (webserver.arg("p213_report",params)=="on"):
   self.taskdevicepluginconfig[1] = True
  else:
   self.taskdevicepluginconfig[1] = False
  try:
   self.taskdevicepluginconfig[2] = int(webserver.arg("p213_freq",params))
  except Exception as e:
   self.taskdevicepluginconfig[2] = 1000
  if self.taskdevicepluginconfig[2] <= 0:
   self.taskdevicepluginconfig[2] = 1000
  self.sync()
  return True

 def sync(self):
  if self.enabled:
   if self.taskdevicepin[0]>=0:
    v1 = 0
    cs = gpios.GPIO_get_statusid(self.taskdevicepin[0])
    try:
     if cs>-1:
      if gpios.GPIOStatus[cs]["mode"] == "pwm":
       v1 = int(gpios.GPIOStatus[cs]["state"])
    except:
     pass
    if self.taskdevicepluginconfig[0]==True:
       ot = False
       for p in range(len(Settings.Pinout)):
        if str(Settings.Pinout[p]["BCM"])==str(self.taskdevicepin[0]):
         if Settings.Pinout[p]["startupstate"] in [4,5,6,7]:
          ot = True
          break
       if ot==False:
        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pin is not an Output, State preserving disabled")
        self.taskdevicepluginconfig[0] = False
    if v1 != self.uservar[0]:
     if self.taskdevicepluginconfig[0]==True:
      self.set_value(1,int(self.uservar[0]),True)   # restore previous state from uservar
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,self.taskname+": Restoring previous PWM value "+str(self.uservar[0]))
     else:
      self.uservar[0] = v1                      # store actual pin state into uservar
      if self.taskdevicepluginconfig[1]:
       self.plugin_senddata()
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,self.taskname+": Syncing actual PWM value "+str(v1))
    elif self.taskdevicepluginconfig[1]:
       self.plugin_senddata()
    self.initialized = True
   if self.initialized:
    if self.taskdevicepluginconfig[0]==True:
     sps = "en"
    else:
     sps = "dis"
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"State preserving is "+sps+"abled")

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized:
   if self.taskdevicepin[0]>=0:
    try:
     val = int(value)
    except:
     val = 0
    try:
     gpios.HWPorts.output_pwm(self.taskdevicepin[0],val,self.taskdevicepluginconfig[2])
     gpios.GPIO_refresh_status(self.taskdevicepin[0],pstate=val,pluginid=self.PLUGIN_ID, pmode="pwm", logtext="")
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Please set up GPIO type before use "+str(e))
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def plugin_receivedata(self,data):                        # set value based on mqtt input
  if (len(data)>0) and self.initialized and self.enabled:
   self.set_value(1,val,self.taskdevicepluginconfig[1])
#  print("Data received:",data) # DEBUG

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0].strip().lower() in gpiohelper.commandlist:
   res = gpiohelper.gpio_commands(cmd)
  return res
