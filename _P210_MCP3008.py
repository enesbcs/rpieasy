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
 PLUGIN_NAME = "Analog input - MCP3008/3208"
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
    try:
      if self.spi<0 or self.spidnum<0:
        return
    except:
     self.spi = 0
     self.spidnum = 0
    self.ports = "SPI"+str(self.spi)+"/"+str(self.spidnum)+" CH"+str(self.taskdevicepluginconfig[2])
    try:
     if int(self.taskdevicepluginconfig[3]) == 0:
      self.taskdevicepluginconfig[3] = 3008
    except:
      self.taskdevicepluginconfig[3] = 3008
    try:
      self.adc = ADC.request_adc_device(int(self.spi),int(self.spidnum),dtype=int(self.taskdevicepluginconfig[3]))
      self.initialized = self.adc.initialized
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ADC can not be initialized! "+str(e))
      self.initialized = False
  if self.initialized == False or self.enabled==False:
     self.ports = ""

 def webform_load(self): # create html page for settings
    options = ["MCP3008","MCP3208"]
    optionvalues = [3008,3208]
    webserver.addFormSelector("ADC type","p210_type",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[3]))
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
   par = webserver.arg("p210_chan",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[2] = int(par)

   par = webserver.arg("p210_type",params)
   try:
    self.taskdevicepluginconfig[3] = int(par)
   except:
    self.taskdevicepluginconfig[3] = 0
   if self.taskdevicepluginconfig[3] == 0:
    self.taskdevicepluginconfig[3] = 3008

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
