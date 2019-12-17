#!/usr/bin/env python3
#############################################################################
####################### PiAnalog plugin for RPIEasy #########################
#############################################################################
#
# Based on the Pi_Analog library:
#  https://github.com/simonmonk/pi_analog
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import webserver
import lib.pi_analog.PiAnalog as Analog

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 2
 PLUGIN_NAME = "Input - PiAnalog (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "Analog"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.timer100ms = False
  self.readinprogress = False
  self.adc = None

 def webform_load(self): # create html page for settings
  webserver.addFormNote("Pin1 is A, Pin2 is B, for wiring, see <a href='https://github.com/simonmonk/pi_analog'>https://github.com/simonmonk/pi_analog</a>")
  choice0 = self.taskdevicepluginconfig[0]
  options = ["Analog","Resistance","Thermistor"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Result Type","p002_type",len(options),options,optionvalues,None,choice0)
  webserver.addFormFloatNumberBox("C1 capacitor", "p002_c1", self.taskdevicepluginconfig[1], 0, 1000000.0)
  webserver.addUnit("uF")
  webserver.addFormNumericBox("R1 resistor","p002_r1",self.taskdevicepluginconfig[2])
  webserver.addUnit("Ohm")
  webserver.addFormFloatNumberBox("Vt voltage (digital HIGH level)", "p002_vt", self.taskdevicepluginconfig[3], 0, 3.3)
  webserver.addUnit("V")
  webserver.addFormNote("Settings below are only valid for thermistor type!")
  webserver.addFormNumericBox("Thermistor resistance","p002_tr",self.taskdevicepluginconfig[4])
  webserver.addUnit("Ohm")
  webserver.addFormNumericBox("Thermistor Beta","p002_tb",self.taskdevicepluginconfig[5])
  return True

 def webform_save(self,params): # process settings post reply
  par1 = webserver.arg("p002_type",params)
  try:
   self.taskdevicepluginconfig[0] = int(par1)
  except:
   self.taskdevicepluginconfig[0] = 0
  par1 = webserver.arg("p002_c1",params)
  try:
   self.taskdevicepluginconfig[1] = float(par1)
  except:
   self.taskdevicepluginconfig[1] = 0.33
  par1 = webserver.arg("p002_r1",params)
  try:
   self.taskdevicepluginconfig[2] = int(par1)
  except:
   self.taskdevicepluginconfig[2] = 10000
  par1 = webserver.arg("p002_vt",params)
  try:
   self.taskdevicepluginconfig[3] = float(par1)
  except:
   self.taskdevicepluginconfig[3] = 1.35
  par1 = webserver.arg("p002_tr",params)
  try:
   self.taskdevicepluginconfig[4] = int(par1)
  except:
   self.taskdevicepluginconfig[4] = 1000
  par1 = webserver.arg("p002_tb",params)
  try:
   self.taskdevicepluginconfig[5] = int(par1)
  except:
   self.taskdevicepluginconfig[5] = 3800
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.initialized=False
  try:
   if str(self.taskdevicepluginconfig[1])=="" or str(self.taskdevicepluginconfig[1])=="0":
    self.taskdevicepluginconfig[1]=0.33
  except:
    self.taskdevicepluginconfig[1]=0.33
  try:
   if str(self.taskdevicepluginconfig[2])=="" or str(self.taskdevicepluginconfig[2])=="0":
    self.taskdevicepluginconfig[2]=10000
  except:
    self.taskdevicepluginconfig[2]=10000
  try:
   if str(self.taskdevicepluginconfig[3])=="" or str(self.taskdevicepluginconfig[3])=="0":
    self.taskdevicepluginconfig[3]=1.35
  except:
    self.taskdevicepluginconfig[3]=1.35
  try:
   if str(self.taskdevicepluginconfig[4])=="" or str(self.taskdevicepluginconfig[4])=="0":
    self.taskdevicepluginconfig[4]=1000
  except:
    self.taskdevicepluginconfig[4]=1000
  try:
   if str(self.taskdevicepluginconfig[5])=="" or str(self.taskdevicepluginconfig[5])=="0":
    self.taskdevicepluginconfig[5]=3800
  except:
    self.taskdevicepluginconfig[5]=3800
  if self.enabled and self.taskdevicepin[0]>=0 and self.taskdevicepin[1]>=0:
   self.readinprogress = False
   try:
    self.adc = Analog.PiAnalog(gpioinit=False,a_pin=self.taskdevicepin[0],b_pin=self.taskdevicepin[1],C=self.taskdevicepluginconfig[1],R1=self.taskdevicepluginconfig[2],Vt=self.taskdevicepluginconfig[3])
    self.initialized = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PiAnalog init error: "+str(e))

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled and self.readinprogress==False and (self.adc is not None):
    self.readinprogress = True
    try:
     if self.taskdevicepluginconfig[0] == 0:
      self.set_value(1,self.adc.analog_read(),False)
     elif self.taskdevicepluginconfig[0] == 1:
      self.set_value(1,self.adc.read_resistance(),False)
     elif self.taskdevicepluginconfig[0] == 2:
      self.set_value(1,self.adc.read_temp_c(self.taskdevicepluginconfig[5],self.taskdevicepluginconfig[4]),False)
    except:
     pass
    self.plugin_senddata()
    self._lastdataservetime = rpieTime.millis()
    self.readinprogress = False
    result = True
  return result
