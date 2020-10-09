#!/usr/bin/env python3
#############################################################################
##################### BLE Scanner plugin for RPIEasy ########################
#############################################################################
#
# Can be used when BLE compatible Bluetooth dongle, and BluePy is installed.
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import Settings
import lib.lib_blescan as BLEScanner
import lib.lib_blehelper as BLEHelper

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 520
 PLUGIN_NAME = "Environment - BLE Scanner (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "Online"
 PLUGIN_VALUENAME2 = "RSSI"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_BLE
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.readinprogress = 0
  self._lastdataservetime = 0
  self._nextdataservetime = 0
  self.blescanner = None
  self.blestatus = None

 def webform_load(self): # create html page for settings
  bledevs = BLEHelper.find_hci_devices()
  options = []
  optionvalues = []
  if bledevs:
   for bd in bledevs:
    options.append(bd)
    try:
     optionvalues.append(int(bd[3:]))
    except:
     optionvalues.append(bd[3:])
  webserver.addFormSelector("Local Device","plugin_520_dev",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[2]))
  webserver.addFormTextBox("Remote Device Address","plugin_520_addr",str(self.taskdevicepluginconfig[0]),20)
  webserver.addFormCheckBox("Add RSSI value for non-Domoticz system","plugin_520_rssi",self.taskdevicepluginconfig[1])
  webserver.addFormNote("For Domoticz it's integrated with online value!")
  webserver.addFormFloatNumberBox("Timeout","plugin_520_tout",float(self.taskdevicepluginconfig[3]),0,60)
  webserver.addUnit("s")
  options = ["State","State or RSSI"]
  optionvalues = ["0","1"]
  webserver.addFormSelector("Report on change of","plugin_520_rep",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[4]))
  return True

 def webform_save(self,params): # process settings post reply
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_520_addr",params)).strip().lower()
  self.taskdevicepluginconfig[1] = (webserver.arg("plugin_520_rssi",params)=="on")
  try:
   self.taskdevicepluginconfig[2] = int(webserver.arg("plugin_520_dev",params))
  except:
   self.taskdevicepluginconfig[2] = 0
  try:
   self.taskdevicepluginconfig[3] = float(webserver.arg("plugin_520_tout",params))
  except:
   self.taskdevicepluginconfig[3] = 5
  try:
   self.taskdevicepluginconfig[4] = int(webserver.arg("plugin_520_rep",params))
  except:
   self.taskdevicepluginconfig[4] = 0
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = 0
  if self.taskdevicepluginconfig[1]:
   self.valuecount = 2
   self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  else:
   self.valuecount = 1
   self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  try:
     devnum = int(self.taskdevicepluginconfig[2])
     self.blestatus  = BLEHelper.BLEStatus[devnum] #devnum!
  except:
     pass
  c = 0
  while self.blestatus.isscaninprogress():
#   print(c)
   c += 1
   time.sleep(0.5)
   if c>10:
    break
  if self.enabled:
    try:
     self.blescanner = BLEScanner.request_blescan_device(devnum,self.taskdevicepluginconfig[3]) #params
     self.blestatus.requestimmediatestopscan = self.blescanner.stop
     self.initialized = True
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"BLE scan init ok")
     if self.interval>4:
      self._lastdataservetime = rpieTime.millis() - ((self.interval-4)*1000)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE scan init error: "+str(e))
     self.initialized = False
  else:
    self.initialized = False

 def plugin_read(self):
   result = False
   if self.enabled and self.initialized and self.readinprogress==0:
    self.readinprogress=1
    if self.blestatus.norequesters() and self.blestatus.nodataflows():
     if self.blestatus.isscaninprogress()==False:
       self.blestatus.reportscan(1)
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE scan started")
       try:
        result = self.blescanner.scan()
       except Exception as e:
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE scan error: "+str(e))
        result = False
       self.blestatus.reportscan(0)
       self.afterscansync()
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE scan ended")
    self.readinprogress=0
#     if result:
#      self._lastdataservetime = rpieTime.millis()
   return result

 def syncchange(self,force=False): # called after all scanning on the same local dev
#  print("sync ",self.taskindex)#debug
  try:
   rssi = self.blescanner.getdevrssi( str(self.taskdevicepluginconfig[0]) )
  except:
   rssi = -100
#  print(rssi)#debug
  if rssi != -100:
   val = 1
  else:
   val = 0
  changed = False
  if force:
   changed = True
  if (val != int(float(self.uservar[0]))):
   changed = True
  if self.taskdevicepluginconfig[4]==1 and (abs(float(rssi) - float(self.uservar[1])) > 0.9):
   changed = True
  if changed:
   self.set_value(1,val,False,suserssi=rssi)
   if self.taskdevicepluginconfig[1]:
    self.set_value(2,rssi,False,suserssi=rssi)
   else:
    self.uservar[1] = float(rssi)
   self.plugin_senddata(puserssi=rssi)
  self._lastdataservetime = rpieTime.millis()

 def afterscansync(self):
  for x in range(0,len(Settings.Tasks)):
   if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
    if (Settings.Tasks[x].enabled):
      if (Settings.Tasks[x].pluginid==520) and (str(self.taskdevicepluginconfig[2]) == str(Settings.Tasks[x].taskdevicepluginconfig[2])): # blescanner plugin
       try:
        Settings.Tasks[x].syncchange()
       except:
        pass

