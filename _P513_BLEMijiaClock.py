#!/usr/bin/env python3
#############################################################################
################### BLE Mijia Clock plugin for RPIEasy ######################
#############################################################################
#
# Xiaomi Mijia LYWSD02 Bluetooth Clock+Temperature/Humidity Sensor plugin.
# Can be used when BLE compatible Bluetooth dongle, and BluePy is installed.
#
# Based on:
#  https://github.com/h4/lywsd02
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
from lywsd02 import Lywsd02Client

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 513
 PLUGIN_NAME = "Environment - BLE Xiaomi LYWSD02 Clock&Hygrometer (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Humidity"
 PLUGIN_VALUENAME3 = "Battery"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_BLE
  self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
  self.valuecount = 2
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.connected = False
  self.formulaoption = True
  self.BLEPeripheral = False
#  self.conninprogress = False
  self.readinprogress = False
  self.battery = 0
  self.lastbatteryreq = 0
  self._lastdataservetime = 0
  self._nextdataservetime = 0

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Device Address","plugin_513_addr",str(self.taskdevicepluginconfig[0]),20)
  webserver.addFormNote("Enable blueetooth then <a href='blescanner'>scan LYWSD02 address</a> first.")
  webserver.addFormCheckBox("Add Battery value for non-Domoticz system","plugin_513_bat",self.taskdevicepluginconfig[1])
  return True

 def webform_save(self,params): # process settings post reply
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_513_addr",params)).strip()
  self.taskdevicepluginconfig[1] = (webserver.arg("plugin_513_bat",params)=="on")
  if self.taskdevicepluginconfig[1]:
   self.valuecount = 3
   self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  else:
   self.valuecount = 2
   self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.timer1s = False
  self.readinprogress = 0
#  self.connected = False
#  self.uservar[0] = 0
#  self.uservar[1] = 0
  if self.enabled:
   try:
    self.BLEPeripheral = Lywsd02Client(str(self.taskdevicepluginconfig[0]),data_request_timeout=int(self.interval))
    self.initialized = True
    self.connected = True
    time.sleep(1)
   except:
    self.initialized = False

 def plugin_read(self):
   result = False
   if self.enabled and self.initialized and self.readinprogress==0:
     self.readinprogress  = 1
     try:
      self.battery = int(self.BLEPeripheral.battery)
      self.set_value(1,float(self.BLEPeripheral.temperature),False)
      if self.taskdevicepluginconfig[1]:
       self.set_value(2,float(self.BLEPeripheral.humidity),False)
       self.set_value(3,self.battery,False,susebattery=self.battery)
      else:
       self.set_value(2,float(self.BLEPeripheral.humidity),False,susebattery=self.battery)
      self.plugin_senddata(pusebattery=self.battery)
      self._lastdataservetime = rpieTime.millis()
      result = True
#      print(self.uservar)
     except Exception as e:
      time.sleep(3)
      pass # print("LYWSD read error: "+str(e))
     self.readinprogress = 0
   return result
