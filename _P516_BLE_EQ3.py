#!/usr/bin/env python3
#############################################################################
###################### BLE EQ3 plugin for RPIEasy ###########################
#############################################################################
#
# EQ3 Bluetooth smart thermostats plugin.
# Can be used when BLE compatible Bluetooth dongle, and BluePy is installed.
#
# Based on:
#  https://github.com/rytilahti/python-eq3bt
#
# Available commands:
#  eq3,taskname,sync
#  eq3,taskname,mode,closed
#  eq3,taskname,mode,open
#  eq3,taskname,mode,auto
#  eq3,taskname,mode,manual
#  eq3,taskname,temp,20.5
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
from eq3bt import Thermostat, Mode
import lib.lib_blehelper as BLEHelper

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 516
 PLUGIN_NAME = "Thermostat - BLE EQ3 (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "TargetTemp"
 PLUGIN_VALUENAME2 = "Mode"
 PLUGIN_VALUENAME3 = "TempOffset"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_BLE
  self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  self.valuecount = 3
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.thermostat = None
  self.readinprogress = False
  self.battery = 0
  self._lastdataservetime = 0
  self._nextdataservetime = 0
  self.blestatus = None

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Device Address","plugin_516_addr",str(self.taskdevicepluginconfig[0]),20)
  webserver.addFormNote("Enable blueetooth then <a href='blescanner'>scan EQ3 address</a> first.")
  webserver.addFormNote("!!!This plugin WILL NOT work with ble scanner plugin!!!")
  return True

 def webform_save(self,params): # process settings post reply
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_516_addr",params)).strip().lower()
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = 0
  if self.enabled:
   try:
     self.blestatus  = BLEHelper.BLEStatus[0] # 0 is hardwired in library
     self.blestatus.registerdataprogress(self.taskindex) # needs continous access
   except:
     pass
   self.ports = str(self.taskdevicepluginconfig[0])
   try:
    self.thermostat = Thermostat(str(self.taskdevicepluginconfig[0]))
    self.initialized = True
    time.sleep(1)
   except:
    self.initialized = False
   if self.interval>2:
    nextr = self.interval-2
   else:
    nextr = 0
   self._lastdataservetime = rpieTime.millis()-(nextr*1000)
  else:
   self.ports = ""

 def plugin_exit(self):
  try:
     self.blestatus.unregisterdataprogress(self.taskindex)
     if self.thermostat._conn is not None:
      self.thermostat._conn.__exit__()
  except:
     pass

 def plugin_read(self):
   result = False
   if self.enabled and self.initialized and self.readinprogress==0:
     self.readinprogress  = 1
     try:
      self.thermostat.update()
      time.sleep(0.1)
      if self.thermostat.low_battery:
       self.battery = 10
      else:
       self.battery = 100
      self.set_value(1,float(self.thermostat.target_temperature),False)
      self.set_value(2,int(self.thermostat.mode),False)
      self.set_value(3,float(self.thermostat.temperature_offset),False,susebattery=self.battery)
      self.plugin_senddata(pusebattery=self.battery)
      self._lastdataservetime = rpieTime.millis()
      result = True
     except Exception as e:
      print("EQ3 read error: "+str(e))
      time.sleep(3)
     self.readinprogress = 0
   return result

 def plugin_write(self,cmd): # handle incoming commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if self.initialized==False:
   return False
  if cmdarr[0] == "eq3":
   try:
    rname = cmdarr[1].strip()
   except:
    rname = ""
   if rname.lower() != self.gettaskname().lower():
    return False # command arrived to another task, skip it
   if cmdarr[2] == "sync":
    if self.thermostat is not None:
     try:
      self.thermostat.update()
      jstruc = {"target temperature": self.thermostat.target_temperature,"mode": self.thermostat.mode_readable}
      res = str(jstruc).replace("'",'"').replace(', ',',\n')
      res = res.replace("{","{\n").replace("}","\n}")
     except Exception as e:
      print(e)
    return res
   elif cmdarr[2]=="mode":
    mode = ""
    try:
     mode = str(cmdarr[3].strip()).lower()
    except:
     mode = ""
    tmode = -1
    if mode == "closed":
     tmode = Mode.Closed
    elif mode == "open":
     tmode = Mode.Open
    elif mode == "auto":
     tmode = Mode.Auto
    elif mode == "manual":
     tmode = Mode.Manual
    elif mode == "away":
     tmode = Mode.Away
    elif mode == "boost":
     tmode = Mode.Boost
    if (self.thermostat is not None) and int(tmode)>-1:
     try:
      self.thermostat.mode = tmode
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EQ3 mode "+str(mode))
      res = True
     except Exception as e:
      print(e)
   elif cmdarr[2]=="temp":
    temp = -1
    try:
     temp = misc.str2num(cmdarr[3].strip())
    except:
     temp = -1
    if (self.thermostat is not None) and temp>4 and temp<31:
     try:
      self.thermostat.target_temperature = temp
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EQ3 target temperature "+str(temp))
      res = True
     except Exception as e:
      print(e)
  return res
