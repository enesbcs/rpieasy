#!/usr/bin/env python3
#############################################################################
################## PCF8591 ADC/DAC plugin for RPIEasy #######################
#############################################################################
#
#
# Available commands:
#   PCFDAC,<port>,<value>       - AOUT port can be 1-8 (which is mapped internally to 0x48-0x4F automatically), value can be 0-255
#                                 (There are one analog output at every PCF8591, and 8 can be used on an I2C bus at a time)
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
import lib.lib_pcfadrouter as lib_pcfadrouter

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 7
 PLUGIN_NAME = "Extra IO - PCF8591 ADC/DAC (TESTING)"
 PLUGIN_VALUENAME1 = "Analog"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.ports = 0
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = True
  self.formulaoption = True
  self.recdataoption = False
  self.pcf = None
  self.i2ca = 0
  self.rpin = -1
  self.i2cport = -1

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
      i2ca, self.rpin = lib_pcfadrouter.get_pcfad_pin_address(pinnum)
      self.pcf = lib_pcfadrouter.request_pcfad_device(pinnum)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCF device requesting failed: "+str(e))
      self.pcf = None
   if self.pcf is None or self.pcf.initialized==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCF can not be initialized! ",self.pcf.initialized)
   else:
    self.initialized = True
    self.readinprogress = 0
    try:
     self.uservar[0] = self.pcf.ADread(self.rpin)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCF read failed:"+str(e))
    try:
     self.ports = str(self.taskdevicepluginconfig[0])
    except:
     self.ports = 0
  else:
   self.ports = 0

 def webform_load(self): # create html page for settings
  webserver.addFormNumericBox("Port","p007_pnum",self.taskdevicepluginconfig[0],1,32)
  webserver.addFormNote("First extender 1-4 (0x48), Second 5-8 (0x49)...")
  return True

 def webform_save(self,params): # process settings post reply
   p2 = self.taskdevicepluginconfig[0]
   par = webserver.arg("p007_pnum",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
   except:
    self.taskdevicepluginconfig[0] = 0
   if p2!=self.taskdevicepluginconfig[0]:
    self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled and self.readinprogress==0:
    self.readinprogress = 1
    try:
     result = self.pcf.ADread(self.rpin)
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
  if cmdarr[0] == "pcfdac" and self.initialized:
   pin = -1
   val = -1
   pcfout = None
   try:
    pin = int(cmdarr[1].strip())
    pcfout = lib_pcfadrouter.request_pcfad_device_byaddr(0x47+pin) # 1-8 = 0x48-0x4F
    val = int(cmdarr[2].strip())
   except:
    pin = -1
    trpin = -1
   if pin>-1 and pcfout is not None:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"PCFDAC"+str(pin)+" set to "+str(val))
    try:
     pcfout.DAwrite(val)
     res = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PCFDAC"+str(pin)+": "+str(e))
   return res
  return res
