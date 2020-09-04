#!/usr/bin/env python3
#############################################################################
####################### BLE CGG1 plugin for RPIEasy #########################
#############################################################################
#
# Xiaomi Cleargrass CGG1 Bluetooth Temperature/Humidity Sensor plugin.
# Can be used when BLE compatible Bluetooth dongle, and BluePy is installed.
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
from bluepy import btle
import threading
import time
from random import uniform
import lib.lib_blehelper as BLEHelper

TEMP_HUM_READ_HANDLE = [0x1e]
CGG_DATA = '00000100-0000-1000-8000-00805f9b34fb'

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 518
 PLUGIN_NAME = "Environment - BLE Xiaomi CGG1 Hygrometer (EXPERIMENTAL)"
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
  self.timeroptional = True
  self.connected = False
  self.formulaoption = True
  self.BLEPeripheral = False
  self.cproc = False
  self.waitnotifications = False
  self.conninprogress = False
  self.readinprogress = False
  self.battery = 0
  self.lastbatteryreq = 0
#  self.lastread = 0
  self.preread = 4000
  self._lastdataservetime = 0
  self._nextdataservetime = 0
  self.TARR = []
  self.HARR = []
  self.failures = 0
  self.lastrequest = 0
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
  webserver.addFormSelector("Local Device","plugin_518_dev",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[2]))
  webserver.addFormTextBox("Device Address","plugin_518_addr",str(self.taskdevicepluginconfig[0]),20)
  webserver.addFormNote("Enable blueetooth then <a href='blescanner'>scan 'ClearGrass Temp & RH'</a> first.")
#  webserver.addFormCheckBox("Add Battery value for non-Domoticz system","plugin_518_bat",self.taskdevicepluginconfig[1])
  return True

 def webform_save(self,params): # process settings post reply
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_518_addr",params)).strip()
#  self.taskdevicepluginconfig[1] = (webserver.arg("plugin_518_bat",params)=="on")
  try:
   self.taskdevicepluginconfig[2] = int(webserver.arg("plugin_518_dev",params))
  except:
   self.taskdevicepluginconfig[2] = 0
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = False
  self.connected = False
  self.conninprogress = False
  self.waitnotifications = False
  self.lastrequest = 0
  self.TARR = []
  self.HARR = []
  try:
   if self.preread:
    pass
  except:
   self.preread = 4000
  self.uservar[0] = 0
  self.uservar[1] = 0
  if self.enabled:
   self.ports = str(self.taskdevicepluginconfig[0])
   self.timer1s = True
   self.battery = -1
   self._nextdataservetime = rpieTime.millis()-self.preread
   self._lastdataservetime = 0
#   self.lastread = 0
   self.failures = 0
   self._lastdataservetime = rpieTime.millis() - ((self.interval-2)*1000)
   if self.taskdevicepluginconfig[1]:
    self.valuecount = 3
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
   else:
    self.valuecount = 2
    self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
   try:
     devnum = int(self.taskdevicepluginconfig[2])
     self.blestatus  = BLEHelper.BLEStatus[devnum]
   except:
     pass
  else:
   self.ports = ""
   self.timer1s = False

 def timer_once_per_second(self):
  if self.enabled:
   if self._nextdataservetime-rpieTime.millis()<=self.preread:
    if self.conninprogress==False and self.connected==False:
     self.waitnotifications = False
     self.blestatus.unregisterdataprogress(self.taskindex)
     if len(self.taskdevicepluginconfig[0])>10:
      self.cproc = threading.Thread(target=self.connectproc)
      self.cproc.daemon = True
      self.cproc.start()
   return self.timer1s

 def plugin_read(self):
   result = False
   if self.enabled:
     if len(self.TARR)>0 and len(self.HARR)>0:
      try:
       self.set_value(1,self.TARR[-1],False)
       self.set_value(2,self.HARR[-1],False)
       self.plugin_senddata()
       self._lastdataservetime = rpieTime.millis()
       self._nextdataservetime = self._lastdataservetime + (self.interval*1000) - self.preread
       self.failures = 0
      except:
       pass
      if self.interval>10:
       self.disconnect()
      self.TARR = []
      self.HARR = []
     elif (self._nextdataservetime < rpieTime.millis()):
      self.isconnected()

 def connectproc(self):
   try:
    if self.blestatus.isscaninprogress():
     self.blestatus.requeststopscan(self.taskindex)
     return False
   except Exception as e:
    return False
   self.conninprogress = True
   while self.blestatus.norequesters()==False or self.blestatus.nodataflows()==False:
       time.sleep(0.5)
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE line not free for P518! "+str(self.blestatus.dataflow))
   self.blestatus.registerdataprogress(self.taskindex)
   prevstate = self.connected
   try:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE connection initiated to "+str(self.taskdevicepluginconfig[0]))
    time.sleep(uniform(0.4,1.8))
    self.BLEPeripheral = btle.Peripheral(str(self.taskdevicepluginconfig[0]),iface=self.taskdevicepluginconfig[2])
    self.connected = True
    self.failures = 0
    self.BLEPeripheral.setDelegate( TempHumDelegateC1(self.callbackfunc) )
   except Exception as e:
    self.connected = False
#   time.sleep(0.5)
   self.isconnected()
   if self.connected==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE connection failed "+str(self.taskdevicepluginconfig[0]))
    self.blestatus.unregisterdataprogress(self.taskindex)
    self.conninprogress = False
    try:
     self.disconnect()
    except:
     pass
    time.sleep(uniform(1,3))
    self.failures =  self.failures +1
    if self.failures>5:
     if self.interval<120:
      skiptime = self.interval*5000
     else:
      skiptime = self.interval
     self._nextdataservetime = rpieTime.millis()+(skiptime)
     self._lastdataservetime = self._nextdataservetime
    return False
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE connected to "+str(self.taskdevicepluginconfig[0]))
    self.waitnotifications = True
    time.sleep(0.1)
    self.blestatus.unregisterdataprogress(self.taskindex)
#    self.get_battery_value()
#    rpieTime.addsystemtimer(3,self.isconnected,[-1])
   self.conninprogress = False

 def request_temp_hum_value(self,d=None):
  res = False
  if time.time() - self.lastrequest > 2: # make sure to do not make too frequent calls
   self.lastrequest = time.time()
   try:
    ch = self.BLEPeripheral.getCharacteristics(uuid=CGG_DATA)[0]
    desc = ch.getDescriptors(forUUID=0x2902)[0]
    desc.write(0x01.to_bytes(2, byteorder="little"), withResponse=True)
    res = True
   except Exception as e:
#    print(e)
    self.blestatus.unregisterdataprogress(self.taskindex)
    res = False
    self.failures+=1
  else:
   res = True # may be not true, test it!
  return res

 def isconnected(self,d=None):
  if self.connected:
   self.connected = self.request_temp_hum_value()
  return self.connected

 def get_battery_value(self):
  return -1

 def callbackfunc(self,temp=None,hum=None):
  self.connected = True
  self.blestatus.unregisterdataprogress(self.taskindex)
  if self.enabled:
   self.TARR.append(temp)
   self.HARR.append(hum)
   if rpieTime.millis()-self._lastdataservetime>=2000:
    self.plugin_read()

 def disconnect(self):
#  print("disconn")
  self.connected = False
  self.waitnotifications = False
  if self.enabled:
   try:
    self.blestatus.unregisterdataprogress(self.taskindex)
    if self.BLEPeripheral is not None:
     self.BLEPeripheral.disconnect()
    self.cproc._stop()
   except:
    pass

 def plugin_exit(self):
  self.disconnect()

# def __exit__(self,type,value,traceback):
#  self.__del__()

class TempHumDelegateC1(btle.DefaultDelegate):
 def __init__(self,callback):
   self.callback = callback
   btle.DefaultDelegate.__init__(self)

 def handleNotification(self, cHandle, data):
   if data is not None:
    temp = None
    hum = None
    try:
        hum_bytes = data[4:]
        temp_bytes = data[:4][2:]
        hum = int.from_bytes(hum_bytes, byteorder='little')/10.0
        temp = int.from_bytes(temp_bytes, byteorder='little')/10.0
    except Exception as e:
     print("Notification error: ",e)
#    print(temp,hum) # DEBUG
    self.callback(temp,hum)
