#!/usr/bin/env python3
#############################################################################
###################### BLE LYWSD03 plugin for RPIEasy #######################
#############################################################################
#
# Xiaomi Mijia LYWSD03 Bluetooth Temperature/Humidity Sensor plugin.
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
import binascii
from random import uniform
import lib.lib_blehelper as BLEHelper

#BATTERY_HANDLE = 0x003A
BATTERY_UUID   = 'EBE0CCC4-7A0A-4B0C-8A1A-6FF2997DA3A6'
TEMP_HUM_WRITE_HANDLE = 0x0038
TEMP_HUM_READ_HANDLE = [0x36,0x3c,0x4b]
TEMP_HUM_WRITE_VALUE = bytearray([0x01, 0x00])

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 517
 PLUGIN_NAME = "Environment - BLE Xiaomi LYWSD03/MHOC401 Hygrometer (EXPERIMENTAL)"
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
  self.BARR = []
  self.failures = 0
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
  webserver.addFormSelector("Local Device","plugin_517_dev",len(options),options,optionvalues,None,int(self.taskdevicepluginconfig[2]))
  webserver.addFormTextBox("Device Address","plugin_517_addr",str(self.taskdevicepluginconfig[0]),20)
  webserver.addFormNote("Enable blueetooth then <a href='blescanner'>scan LYWSD03 address</a> first.")
  webserver.addFormCheckBox("Add Battery value for non-Domoticz system","plugin_517_bat",self.taskdevicepluginconfig[1])
#  webserver.addFormCheckBox("Connect only if BLE local device free","plugin_517_free",self.taskdevicepluginconfig[3])
  webserver.addFormNote("Check if you are using multiple devices and interferences occurs between them.")
  return True

 def webform_save(self,params): # process settings post reply
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_517_addr",params)).strip()
  self.taskdevicepluginconfig[1] = (webserver.arg("plugin_517_bat",params)=="on")
  try:
   self.taskdevicepluginconfig[2] = int(webserver.arg("plugin_517_dev",params))
  except:
   self.taskdevicepluginconfig[2] = 0
#  self.taskdevicepluginconfig[3] = str(webserver.arg("plugin_517_free",params)).strip()
  self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = False
  self.connected = False
  self.conninprogress = False
  self.waitnotifications = False
  self.connectcount = 0
  self.TARR = []
  self.HARR = []
  self.BARR = []
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
   self.battery = 255
   self._lastdataservetime = 0
#   self.lastread = 0
   self.failures = 0
   self._nextdataservetime = rpieTime.millis() + (self.interval*1000)
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
#      self.get_battery_value()
#      if self.battery==-1:
#       self.get_battery_value()
#       if self.battery==-1:
#        self.get_battery_value()
      try:
       self.battery = self.BARR[-1]
      except:
       self.battery=255
      if self.battery is None:
       self.battery=255
      try:
       self.set_value(1,self.TARR[-1],False)
       if self.taskdevicepluginconfig[1]:
        self.set_value(2,self.HARR[-1],False)
        self.set_value(3,self.battery,False,susebattery=self.battery)
       else:
        self.set_value(2,self.HARR[-1],False,susebattery=self.battery)
       self.plugin_senddata(pusebattery=self.battery)
       self._lastdataservetime = rpieTime.millis()
       self._nextdataservetime = self._lastdataservetime + (self.interval*1000)
       self.failures = 0
      except:
       pass
      if self.interval>10:
       self.disconnect()
      self.TARR = []
      self.HARR = []
      self.BARR = []
     elif (self._nextdataservetime < rpieTime.millis()):
      self._nextdataservetime = self._lastdataservetime + uniform(self.preread,self.preread*2.5)
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
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE,"BLE line not free for P517! "+str(self.blestatus.dataflow))
   self.blestatus.registerdataprogress(self.taskindex)
   prevstate = self.connected
   try:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE connection initiated to "+str(self.taskdevicepluginconfig[0]))
    time.sleep(uniform(0.4,1.8))
    self.BLEPeripheral = btle.Peripheral(str(self.taskdevicepluginconfig[0]),iface=self.taskdevicepluginconfig[2])
    self.connected = True
    self.failures = 0
    self.connectcount = 0
    self.BLEPeripheral.setDelegate( TempHumDelegate2(self.callbackfunc) )
   except Exception as e:
#    print(e) # debug
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
    time.sleep(uniform(0.5,1.2))
    self.failures =  self.failures +1
    if self.failures>5:
     if self.interval<120:
      skiptime = self.interval*5000
     else:
      skiptime = self.interval
     self._nextdataservetime = rpieTime.millis()+(skiptime)
#     self._lastdataservetime = self._nextdataservetime
    return False
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE,"BLE connected to "+str(self.taskdevicepluginconfig[0]))
    self.waitnotifications = True
#    self.get_battery_value()
#    rpieTime.addsystemtimer(15,self.deregister,[-1])
    time.sleep(0.1)
    self.blestatus.unregisterdataprogress(self.taskindex)
   self.conninprogress = False

 def request_temp_hum_value(self,d=None):
  res = False
  try:
   if self.BLEPeripheral is not None:
    self.BLEPeripheral.writeCharacteristic(TEMP_HUM_WRITE_HANDLE, TEMP_HUM_WRITE_VALUE)
    res = True
  except Exception as e:
   res = False
   self.blestatus.unregisterdataprogress(self.taskindex)
  return res

 def isconnected(self,d=None):
  if self.connected:
   self.connected = self.request_temp_hum_value()
  return self.connected

 def deregister(self,d=None):
    self.blestatus.unregisterdataprogress(self.taskindex)

 def get_battery_value(self): # now it is not used
  if ((time.time()-self.lastbatteryreq)>600) or (self.battery<=0):
   battery = 0
   try:
    if self.BLEPeripheral is not None:
     ch = self.BLEPeripheral.getCharacteristics(uuid=BATTERY_UUID)[0]
     value = ch.read()
     battery = ord(value) # self.BLEPeripheral.readCharacteristic(BATTERY_HANDLE)[0]
     self.lastbatteryreq = time.time()
   except Exception as e:
    self.blestatus.unregisterdataprogress(self.taskindex)
   try:
    if battery:
     self.battery = int(battery)
   except Exception as e:
    pass
  return self.battery

 def callbackfunc(self,temp=None,hum=None,batt=None):
#  self.connected = True
  self.blestatus.unregisterdataprogress(self.taskindex)
  if self.enabled:
   self.TARR.append(temp)
   self.HARR.append(hum)
   self.BARR.append(batt)
   if rpieTime.millis()-self._lastdataservetime>=2000:
    self.plugin_read()

 def disconnect(self,forceit=False):
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

class TempHumDelegate2(btle.DefaultDelegate):
 def __init__(self,callback):
   self.callback = callback
   btle.DefaultDelegate.__init__(self)

 def handleNotification(self, cHandle, data):
   if (cHandle in TEMP_HUM_READ_HANDLE) and data is not None:
    temp = None
    hum = None
    batt = None
    try:
     received = bytearray(data)
     temp = float(received[1] * 256 + received[0]) / 100
     hum = received[2]
     try:
       battvolt = float(received[4]*256 + received[3]) / 1000
     except:
       battvolt = -1
     batt = min(int(round((battvolt - 2.1),2) * 100), 100)
     if battvolt<=0 or batt<=0:
       batt = 0
    except Exception as e:
     print("Notification error: ",e)
#    print(temp,hum,batt) # DEBUG
    self.callback(temp,hum,batt)
