#!/usr/bin/env python3
#############################################################################
################ PCA9685 PWM extender plugin for RPIEasy ####################
#############################################################################
#
# Available commands:
#  PCAPWM,<pin>,<value>   - Control PCA9685 pwm level 0..4095
#  PCAFRQ,<frequency>     - Set all PWM channel frequency
#
# https://github.com/voidpp/PCA9685-driver/blob/master/pca9685_driver/device.py
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time
from pca9685_driver import Device # sudo pip3 install PCA9685-driver

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 22
 PLUGIN_NAME = "Extra IO - PCA9685"
 PLUGIN_VALUENAME1 = "PWM"
 MAX_PINS = 15
 MAX_PWM = 4095
 MIN_FREQUENCY = 23.0   # Min possible PWM cycle frequency
 MAX_FREQUENCY = 1500.0 # Max possible PWM cycle frequency

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.ports = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = False
  self.pca = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = False
  self.pca = None
  if self.enabled:
   i2cport = -1
   try:
    for i in range(0,2):
     if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
      i2cport = i
      break
   except:
    i2cport = -1
   if i2cport>-1 and int(self.taskdevicepluginconfig[0])>0:
     try:
      freq = int(self.taskdevicepluginconfig[1])
      if freq<self.MIN_FREQUENCY or freq>self.MAX_FREQUENCY:
       freq = self.MAX_FREQUENCY
     except:
       freq = self.MAX_FREQUENCY
     try:
      self.pca = Device(address=int(self.taskdevicepluginconfig[0]),bus_number=int(i2cport))
      if self.pca is not None:
       self.initialized = True
       self.pca.set_pwm_frequency(freq)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCA9685 device init failed: "+str(e))
      self.pca = None
   if self.pca is not None:
    pass

 def webform_load(self): # create html page for settings
  choice1 = int(float(self.taskdevicepluginconfig[0])) # store i2c address
  optionvalues = []
  for i in range(0x40,0x78):
   optionvalues.append(i)
  options = []
  for i in range(len(optionvalues)):
   options.append(str(hex(optionvalues[i])))
  webserver.addFormSelector("Address","p022_adr",len(options),options,optionvalues,None,choice1)
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  webserver.addFormNumericBox("Frequency","p022_freq",self.taskdevicepluginconfig[2],self.MIN_FREQUENCY,self.MAX_FREQUENCY)
  webserver.addUnit("Hz")
  return True

 def webform_save(self,params): # process settings post reply
   cha = False
   par = webserver.arg("p022_adr",params)
   if par == "":
    par = 0x40
   if self.taskdevicepluginconfig[0] != int(par):
    cha = True
   self.taskdevicepluginconfig[0] = int(par)
   par = webserver.arg("p022_freq",params)
   if par == "":
    par = self.MAX_FREQUENCY
   if self.taskdevicepluginconfig[2] != int(par):
    cha = True
   self.taskdevicepluginconfig[2] = int(par)
   if cha:
    self.plugin_init()
   return True

 def plugin_write(self,cmd): # handle incoming commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if self.pca is not None:
   if cmdarr[0] == "pcapwm":
    pin = -1
    val = -1
    try:
     pin = int(cmdarr[1].strip())
     val = int(cmdarr[2].strip())
    except:
     pin = -1
    if pin>-1 and val>=0 and val<=self.MAX_PWM:
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCAPWM"+str(pin)+" set to "+str(val))
     try:
      self.pca.set_pwm(pin, val)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCAPWM"+str(pin)+": "+str(e))
    return True
   if cmdarr[0] == "pcafrq":
    freq = -1
    try:
     freq = int(cmdarr[1].strip())
    except:
     freq = -1
    if (freq>-1) and (freq>=self.MIN_FREQUENCY) and (freq<=self.MAX_FREQUENCY):
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCAFRQ"+str(freq))
     try:
      self.pca.set_pwm_frequency(freq)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCAFRQ"+str(e))
    return True

  return res
