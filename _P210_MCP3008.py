#!/usr/bin/env python3
#############################################################################
######################## MCP3008 plugin for RPIEasy #########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import lib.lib_mcp3008 as ADC
import gpios

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 210
 PLUGIN_NAME = "Analog input - MCP3008"
 PLUGIN_VALUENAME1 = "Analog"

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
    self.ports = "SPI"+str(self.taskdevicepluginconfig[0])+"/"+str(self.taskdevicepluginconfig[1])+" CH"+str(self.taskdevicepluginconfig[2])
    try:
      self.adc = ADC.request_adc_device(int(self.taskdevicepluginconfig[0]),int(self.taskdevicepluginconfig[1]))
      self.initialized = self.adc.initialized
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ADC can not be initialized! "+str(e))
      self.initialized = False
  if self.initialized == False or self.enabled==False:
     self.ports = ""

 def webform_load(self): # create html page for settings
  ok = True
  spichannels = []
  try:
   for i in range(4):
    if gpios.HWPorts.is_spi_usable(i) and gpios.HWPorts.is_spi_enabled(i):
     spichannels.append(i)
  except:
   pass
  options = []
  optionvalues = []
  for i in range(len(spichannels)):
   options.append(str(spichannels[i]))
   optionvalues.append(int(spichannels[i]))
  choice1 = self.taskdevicepluginconfig[0]
  webserver.addFormSelector("SPI bus","p210_bus",len(options),options,optionvalues,None,int(choice1))
  if len(spichannels)<1:
   webserver.addFormNote("No usable SPI channel found, be sure to enable it at <a href='pinout'>hardware settings</a>!")
   ok = False
  if ok:
    choice2 = self.taskdevicepluginconfig[1]
    options = []
    optionvalues = []
    for i in range(4):
     options.append("CE"+str(i))
     optionvalues.append(int(i))
    webserver.addFormSelector("Device number","p210_addr",len(options),options,optionvalues,None,int(choice2))
    choice3 = self.taskdevicepluginconfig[2]
    options = []
    optionvalues = []
    for i in range(8):
     options.append("CH"+str(i))
     optionvalues.append(int(i))
    webserver.addFormSelector("Channel number","p210_chan",len(options),options,optionvalues,None,int(choice3))
    webserver.addFormCheckBox("Oversampling","p210_over",self.timer1s)
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p210_bus",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[0] = int(par)

   par = webserver.arg("p210_addr",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[1] = int(par)

   par = webserver.arg("p210_chan",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[2] = int(par)

   if (webserver.arg("p210_over",params)=="on"):
    self.timer1s = True
   else:
    self.timer1s = False
   self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled:
   self.p210_get_value()
   if len(self.TARR)>0:
    self.set_value(1,(sum(self.TARR) / float(len(self.TARR))),False)
    self.plugin_senddata()
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MCP3008 read failed!")
   result = True
   self.TARR = []
   self._lastdataservetime = rpieTime.millis()
   self._nextdataservetime = self._lastdataservetime + (self.interval*1000)
  return result

 def timer_once_per_second(self):
  if self.initialized and self.enabled:
   if self._nextdataservetime-rpieTime.millis()<=self.preread:
    self.p210_get_value()
  return self.timer1s

 def p210_get_value(self):
  val = -1
  try:
   val = self.adc.ADread(self.taskdevicepluginconfig[2])
  except Exception as e:
   val = -1
  if val != -1:
   self.TARR.append(val)
