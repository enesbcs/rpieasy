#!/usr/bin/env python3
#############################################################################
###################### HX711 plugin for RPIEasy #############################
#############################################################################
#
# Copyright (C) 2023 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
from lib.hx711.hx711 import HX711
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 67
 PLUGIN_NAME = "Weight - HX711 Load Cell [EXPERIMENTAL]"
 PLUGIN_VALUENAME1 = "WeightChanA"
 PLUGIN_VALUENAME2 = "WeightChanB"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  self.valuecount = 2
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.readinprogress = 0
  self._hx = None
  self.initialized = False
  self.offset = [ [1,1], [1,1], [1,1], [1,1] ]

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled and self.taskdevicepin[0]>0 and self.taskdevicepin[1]>0:
     self.readinprogress = 1
     try:
      self._hx = HX711( int(self.taskdevicepin[1]), int(self.taskdevicepin[0]) ) #dout, sck
      self._hx.set_reading_format("MSB","MSB")
      self._hx.reset()
      self.initialized = True
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HX711 init error: "+str(e))
      self.initialized = False
      self._hx = None
     if self._hx is not None:
      try:
        if self.taskdevicepluginconfig[0] != 0:
           self._hx.set_offset_A(self.taskdevicepluginconfig[1])
           ref = 0
           try:
            ref = self.offset[0][0] / self.offset[0][1]
           except:
            ref = 0
           if ref != 0:
            self._hx.set_reference_unit_A(ref)
        if self.taskdevicepluginconfig[2] != 0:
           self._hx.set_offset_B(self.taskdevicepluginconfig[3])
           ref = 0
           try:
            ref = self.offset[1][0] / self.offset[1][1]
           except:
            ref = 0
           if ref != 0:
            self._hx.set_reference_unit_B(ref)
      except:
        pass
     self.readinprogress = 0

 def plugin_exit(self):
  try:
   if self._hx:
    self._hx.power_down()
  except:
   pass

 def __del__(self):
  self.plugin_exit()

 def webform_load(self):
  webserver.addFormNote("1st GPIO is <b>SCK</b> pin which has to be an output, and 2nd GPIO is the <b>DT</b> pin which has to be an input!<br>Make sure to set it up at <a href='pinout'>Pinout settings</a> first!")
  choice1 = self.taskdevicepluginconfig[0]
  options = ["Off","Gain 64","Gain 128"]
  optionvalues = [0,64,128]
  webserver.addFormSubHeader("Measurement Channel A")
  webserver.addFormSelector("Mode","modeChA",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormTextBox("Offset","offsChA",self.taskdevicepluginconfig[1],20)
  webserver.addFormCheckBox("Tare","tareChA",False)
  options = ["Off","Gain 32"]
  optionvalues = [0,32]
  choice1 = self.taskdevicepluginconfig[2]
  webserver.addFormSubHeader("Measurement Channel B")
  webserver.addFormSelector("Mode","modeChB",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormTextBox("Offset","offsChB",self.taskdevicepluginconfig[3],20)
  webserver.addFormCheckBox("Tare","tareChB",False)
  webserver.addFormSubHeader("Calibration Channel A")
  webserver.addFormNumericBox("Point 1","adc1ChA",self.offset[0][0])
  webserver.addHtml("=")
  webserver.addFormTextBox("Value 1","out1ChA",self.offset[0][1],20)
  webserver.addFormSubHeader("Calibration Channel B")
  webserver.addFormNumericBox("Point 1","adc1ChB",self.offset[1][0])
  webserver.addHtml("=")
  webserver.addFormTextBox("Value 1","out1ChB",self.offset[1][1],20)
  return True

 def webform_save(self,params):
  try:
   self.taskdevicepluginconfig[0] = int(webserver.arg("modeChA",params))
   self.taskdevicepluginconfig[1] = float(webserver.arg("offsChA",params))
   self.taskdevicepluginconfig[2] = int(webserver.arg("modeChB",params))
   self.taskdevicepluginconfig[3] = float(webserver.arg("offsChB",params))
  except:
   pass
  try:
   self.offset[0][0] = int(webserver.arg("adc1ChA",params))
   self.offset[0][1] = int(webserver.arg("out1ChA",params))
   self.offset[1][0] = int(webserver.arg("adc1ChB",params))
   self.offset[1][1] = int(webserver.arg("out1ChB",params))
  except:
   pass
  if (webserver.arg("tareChA",params)=="on"):
     try:
      if self._hx:
         while self.readinprogress:
           time.sleep(0.01)
         self.readinprogress = 1
         self._hx.tare_A()
         self.readinprogress = 0
         self.taskdevicepluginconfig[1] = self._hx.get_offset_A()
     except:
      pass
  if (webserver.arg("tareChB",params)=="on"):
     try:
      if self._hx:
         while self.readinprogress:
           time.sleep(0.01)
         self.readinprogress = 1
         self._hx.tare_B()
         self.readinprogress = 0
         self.taskdevicepluginconfig[3] = self._hx.get_offset_B()
     except:
      pass
  self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   if self._hx:
      self._hx.power_up()
      if int(self.taskdevicepluginconfig[0]) != 0: #A
         self._hx.set_gain(self.taskdevicepluginconfig[0])
         value = self._hx.get_weight_A(5)
         self.set_value(1,value,True)
      if int(self.taskdevicepluginconfig[2]) != 0: #B
         value = self._hx.get_weight_B(5)
         self.set_value(2,value,True) #always gain32
      self._hx.power_down()
      self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "tarechan": #a / b
   res = True
   try:
    if cmdarr[0][8] == "a":
      if self._hx:
         while self.readinprogress:
           time.sleep(0.01)
         self.readinprogress = 1
         self._hx.tare_A()
         self.readinprogress = 0
         self.taskdevicepluginconfig[1] = self._hx.get_offset_A()
    elif cmdarr[0][8] == "b":
      if self._hx:
         while self.readinprogress:
           time.sleep(0.01)
         self.readinprogress = 1
         self._hx.tare_B()
         self.readinprogress = 0
         self.taskdevicepluginconfig[3] = self._hx.get_offset_A()
   except:
    pass
  return res
