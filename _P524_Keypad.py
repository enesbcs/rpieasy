#!/usr/bin/env python3
#############################################################################
#################### HT16K33 KeyPad plugin for RPIEasy ######################
#############################################################################
#
# Plugin to scan a 4x3 or 4x4 keypad matrix with pure RPi.GPIO
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import webserver
import lib.keypad.keypad as KeyPad

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 524
 PLUGIN_NAME = "Input - KeyPad GPIO"
 PLUGIN_VALUENAME1 = "ScanCode"

 KEYPAD12 = [
            [17,18,19],
            [33,34,35],
            [49,50,51],
            [65,66,67]
 ]
 KEYPAD16 = [
            [17,18,19,20],
            [33,34,35,36],
            [49,50,51,52],
            [65,66,67,68]
 ]
 DEF_ROW_PINS = [4,17,27,22]
 DEF_COL_PINS = [23,24,25,12]

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = False
  self.timeroptional = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.kptype = 0
  self.keypad = []
  self.rowpins = []
  self.colpins = []
  self.kphander = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.initialized = False
  if self.enabled:
   if len(self.rowpins)<1 or len(self.colpins)<1 or len(self.keypad)<1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Keypad: no data for init")
    return # settings not found
   registered = False
   try:
    if self.kphandler is not None:
     if self.kphandler.isInitialized():
      registered = True
   except:
     self.kphandler = None 
     registered = False
   try:
    self.kphandler = KeyPad.keypad(keypad=self.keypad,row_pins=self.rowpins,col_pins=self.colpins,callback=self.keypadchanged)
    self.kphandler.startscan()
    self.initialized = self.kphandler.isInitialized()
   except Exception as e:
    if self.registered==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Keypad error: "+str(e))
     self.initialized = False
    else:
     self.initialized = True
   if self.initialized:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Keypad init ok")
   else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Keypad init failed")

 def webform_load(self):
  if len(self.colpins) < 1:
   self.colpins = self.DEF_COL_PINS
  if len(self.rowpins) < 1:
   self.rowpins = self.DEF_ROW_PINS
  if len(self.keypad) < 1 or self.kptype==0:
   self.keypad = self.KEYPAD16
   self.kptype = 16

  optionvalues = [16,12]
  options = ["4x4","3x4"]
  webserver.addFormSelector("Type","p524_type",len(options),options,optionvalues,None,self.kptype)
  webserver.addFormNote("Setup Row pins as Input-PullDown, Column pins as Output at <a href='pinout'>Pinout page</a>")

  webserver.addFormPinSelect("Row1 pin","row1pin",self.rowpins[0])
  webserver.addFormPinSelect("Row2 pin","row2pin",self.rowpins[1])
  webserver.addFormPinSelect("Row3 pin","row3pin",self.rowpins[2])
  webserver.addFormPinSelect("Row4 pin","row4pin",self.rowpins[3])
  webserver.addFormPinSelect("Col1 pin","col1pin",self.colpins[0])
  webserver.addFormPinSelect("Col2 pin","col2pin",self.colpins[1])
  webserver.addFormPinSelect("Col3 pin","col3pin",self.colpins[2])
  try:
   cp = self.colpins[3]
  except:
   cp = -1
  webserver.addFormPinSelect("Col4 pin","col4pin",cp)
  webserver.addFormNote("Col4 only used on 4x4 type!")
  return True

 def webform_save(self,params):
   par = str(webserver.arg("p524_type",params))
   if par == "" or par=="0":
    par = 16
   else:
    try:
     self.kptype = int(par)
    except:
     self.kptype = 16
   if self.kptype==16:
    if len(self.colpins)<4:
     self.colpins = self.DEF_COL_PINS
   elif self.kptype==12:
    if len(self.colpins)!=3:
     self.colpins = self.DEF_COL_PINS
     del self.colpins[3]
   if len(self.rowpins)<4:
     self.rowpins = self.DEF_ROW_PINS
   if self.kptype==12:
    self.keypad= self.KEYPAD12
   elif self.kptype==16:
    self.keypad= self.KEYPAD16

   try:
    self.rowpins[0] = int(webserver.arg("row1pin",params))
   except:
    self.rowpins[0] = -1
   try:
    self.rowpins[1] = int(webserver.arg("row2pin",params))
   except:
    self.rowpins[1] = -1
   try:
    self.rowpins[2] = int(webserver.arg("row3pin",params))
   except:
    self.rowpins[2] = -1
   try:
    self.rowpins[3] = int(webserver.arg("row4pin",params))
   except:
    self.rowpins[3] = -1

   try:
    self.colpins[0] = int(webserver.arg("col1pin",params))
   except:
    self.colpins[0] = -1
   try:
    self.colpins[1] = int(webserver.arg("col2pin",params))
   except:
    self.colpins[1] = -1
   try:
    self.colpins[2] = int(webserver.arg("col3pin",params))
   except:
    self.colpins[2] = -1
   if self.kptype==16:
    try:
     self.colpins[3] = int(webserver.arg("col4pin",params))
    except:
     self.colpins[3] = -1
   try:
    self.plugin_init()
   except:
    pass
   return True

 def plugin_read(self):
  return True

 def plugin_exit(self):
   try:
    self.kphandler.stopscan()
   except:
    pass

 def keypadchanged(self,key):
    self.set_value(1,int(key),True)
    self._lastdataservetime = rpieTime.millis()
