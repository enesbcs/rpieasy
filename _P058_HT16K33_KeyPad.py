#!/usr/bin/env python3
#############################################################################
#################### HT16K33 KeyPad plugin for RPIEasy ######################
#############################################################################
#
# Plugin to scan a 13x3 key pad matrix chip HT16K33
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import webserver
import lib.HT16K33.Adafruit_LEDBackpack as HT16K33

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 58
 PLUGIN_NAME = "Input - HT16K33 KeyPad"
 PLUGIN_VALUENAME1 = "ScanCode"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.ht16 = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.initialized = False
  self.timer100ms = False
  if self.enabled:
   try:
     i2cl = self.i2c
   except:
     i2cl = -1
   try:
    i2cport = gpios.HWPorts.geti2clist()
    if i2cl==-1:
      i2cl = int(i2cport[0])
   except:
    i2cport = []
   if len(i2cport)>0 and i2cl>-1:
     try:
      i2ca = int(self.taskdevicepluginconfig[0])
     except:
      i2ca = 0
     if i2ca>0:
      try:
       self.ht16 = HT16K33.LEDBackpack(address=int(i2ca),i2cbusnum=i2cl)
       self.timer100ms = True
       self.initialized = True
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 device requesting failed: "+str(e))
       self.ht16 = None


 def webform_load(self):
  choice1 = int(float(self.taskdevicepluginconfig[0])) # store i2c address
  optionvalues = []
  for i in range(0x70, 0x78):
   optionvalues.append(i)
  options = []
  for i in range(len(optionvalues)):
   options.append(str(hex(optionvalues[i])))
  webserver.addFormSelector("Address","p058_adr",len(options),options,optionvalues,None,choice1)
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params):
   cha = False
   par = webserver.arg("p058_adr",params)
   if par == "":
    par = 0x70
   if self.taskdevicepluginconfig[0] != int(par):
    cha = True
   self.taskdevicepluginconfig[0] = int(par)
   if cha:
    self.plugin_init()
   return True

 def plugin_read(self):
  result = False
  if self.initialized:
   result = True
  return result

 def timer_ten_per_second(self):
   try:
    val = self.getkeys()
   except:
    val = 0
   if int(val) != int(float(self.uservar[0])):
    self.set_value(1,int(val),True)
    self._lastdataservetime = rpieTime.millis()

 def getkeys(self):
  if self.initialized and self.enabled:
   key = [0,0,0]
   for i in range(0,3):
    key[i] = self.ht16.getKeys(i)
   for i in range(0,3):
    mask = 1
    for k in range(0,12):
      if (key[i] & mask):
       _keydown = 16*(i+1)+(k+1)
       return _keydown
      mask = mask << 1
  _keydown = 0
  return _keydown
