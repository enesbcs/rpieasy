#!/usr/bin/env python3
#############################################################################
#################### Thermosensors plugin for RPIEasy #######################
#############################################################################
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import lib.lib_spithermo as Thermo

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 39
 PLUGIN_NAME = "Environment - Thermosensors"
 PLUGIN_VALUENAME1 = "Temperature"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SPI
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.ports = 0
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self.adc = None
  self._nextdataservetime = 0
  self.lastread = 0
  self.samples = 3
  self.preread = self.samples*1000 # 3 * 1 sec
  self.TARR = []

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.TARR = []
  if self.enabled:
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval
    self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    self.preread = self.samples*1000
    try:
      if self.spi<0 or self.spidnum<0:
        return
    except:
     self.spi = 0
     self.spidnum = 0
    self.ports = "SPI"+str(self.spi)+"/"+str(self.spidnum)
    try:
     if str(self.taskdevicepluginconfig[3]).strip() == "" or str(self.taskdevicepluginconfig[3]).strip() == "0":
      self.taskdevicepluginconfig[3] = 6675
    except:
      self.taskdevicepluginconfig[3] = 6675
    try:
      self.adc = Thermo.request_thermo_device(int(self.spi),int(self.spidnum),dtype=int(self.taskdevicepluginconfig[3]))
      self.initialized = self.adc.initialized
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ADC can not be initialized! "+str(e))
      self.initialized = False
  if self.initialized == False or self.enabled==False:
     self.ports = ""

 def webform_load(self): # create html page for settings
    options = ["Max6675","Max31855"]
    optionvalues = [6675,31855]
    webserver.addFormSelector("Adapter type","p039_type",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[3]))
    choice3 = self.taskdevicepluginconfig[2]
#    webserver.addFormCheckBox("Oversampling","p039_over",self.timer1s)
    webserver.addFormNote("Hardware SPI supported: connect module SCK to SPI SCLK, CS to SPI CS0/CS1/CS2, SO to SPI MISO")
    return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p039_type",params)
   try:
    self.taskdevicepluginconfig[3] = int(par)
   except:
    self.taskdevicepluginconfig[3] = 0
   if self.taskdevicepluginconfig[3] == 0:
    self.taskdevicepluginconfig[3] = 6675

   if (webserver.arg("p039_over",params)=="on"):
    self.timer1s = True
   else:
    self.timer1s = False
   self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled:
   self.p039_get_value()
   if len(self.TARR)>0:
    self.set_value(1,(sum(self.TARR) / float(len(self.TARR))),False)
    self.plugin_senddata()
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MAX thermocouple read failed!")
   result = True
   self.TARR = []
   self._lastdataservetime = rpieTime.millis()
   self._nextdataservetime = self._lastdataservetime + (self.interval*1000)
  return result

 def timer_once_per_second(self):
  if self.initialized and self.enabled:
   if self._nextdataservetime-rpieTime.millis()<=self.preread:
    self.p039_get_value()
  return self.timer1s

 def p039_get_value(self):
  val = -1
  try:
   val = self.adc.read()
  except Exception as e:
   val = -1
  if val != -1:
   self.TARR.append(val)
