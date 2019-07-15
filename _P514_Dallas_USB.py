#!/usr/bin/env python3
#############################################################################
################### Dallas onewire USB plugin for RPIEasy ###################
#############################################################################
#
# Based on pydigitemp and pyserial
#
# https://www.instructables.com/id/Quick-Digital-Thermometer-Using-Cheap-USB-to-TTL-C/
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import serial
import serial.tools.list_ports
import digitemp.master
import digitemp.device

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 514
 PLUGIN_NAME = "Environment - DS1820 USB"
 PLUGIN_VALUENAME1 = "Temperature"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SER
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.sensor = None
  self.bus = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = False
  try:
   if self.bus is not None:
    self.bus.close()
    self.bus._unlock()
  except:
    pass
  if self.enabled or enableplugin:
   if (str(self.taskdevicepluginconfig[0]) != "0") and (str(self.taskdevicepluginconfig[0]).strip() != ""):
    try:
     self.bus = digitemp.master.UART_Adapter(str(self.taskdevicepluginconfig[0]))
    except:
     pass
    if (str(self.taskdevicepluginconfig[1]) != "0") and (str(self.taskdevicepluginconfig[1]).strip() != ""):
     try:
      if self.taskdevicepluginconfig[1].startswith("10"):
       self.sensor = digitemp.device.DS1820(self.bus, rom=str(self.taskdevicepluginconfig[1]))
       self.initialized = True
      elif self.taskdevicepluginconfig[1].startswith("28"):
       self.sensor = digitemp.device.DS18B20(self.bus, rom=str(self.taskdevicepluginconfig[1]))
       self.initialized = True
      elif self.taskdevicepluginconfig[1].startswith("22"):
       self.sensor = digitemp.device.DS1822(self.bus, rom=str(self.taskdevicepluginconfig[1]))
       self.initialized = True
      else:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"DS Type uknown for "+self.taskdevicepluginconfig[1])
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"USB-Dallas "+str(e))
      self.initialized = False
   if self.initialized==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"USB-Dallas device can not be initialized!")
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"USB-Dallas device initialized!")

 def webform_load(self):
  choice0 = self.taskdevicepluginconfig[0]
  options0 = self.serial_portlist()
  if len(options0)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p514_addr",False)
   for o in range(len(options0)):
    webserver.addSelector_Item(options0[o],options0[o],(str(options0[o])==str(choice0)),False)
   webserver.addSelector_Foot()

   choice1 = self.taskdevicepluginconfig[1]
   options1 = self.find_dsb_devices()
   if len(options1)>0:
    webserver.addHtml("<tr><td>Device Address:<td>")
    webserver.addSelector_Head("p514_id",True)
    for o in range(len(options1)):
     webserver.addSelector_Item(options1[o],options1[o],(str(options1[o])==str(choice1)),False)
    webserver.addSelector_Foot()
   else:
    webserver.addFormNote("No DS18B20 found on bus!")
  else:
   webserver.addFormNote("No serial port found!")
  webserver.addFormNote("You have to connect the Ds18B20 through an USB-Serial adapter!")
  return True

 def webform_save(self,params):
  par = str(webserver.arg("p514_addr",params))
  p1 = str(self.taskdevicepluginconfig[0])
  self.taskdevicepluginconfig[0] = par
  par = str(webserver.arg("p514_id",params))
  p2 = str(self.taskdevicepluginconfig[1])
  self.taskdevicepluginconfig[1] = str(par)
  if p1 != str(self.taskdevicepluginconfig[0]) or p2 != str(self.taskdevicepluginconfig[1]):
   self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   try:
    succ, temp = self.read_temperature()
    if succ:
     self.set_value(1,temp,True)
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Dallas read error!")
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Dallas read error! "+str(e))
    self.enabled = False
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def serial_portlist(self):
  ports = []
  try:
   for port in serial.tools.list_ports.comports():
    ports.append(str(port.device))
  except:
   pass
  return ports

 def find_dsb_devices(self):
  self.readinprogress = 1
  try:
    if self.bus is not None:
     self.bus.close()
     self.bus_unlock()
     self.initialized = False
  except:
    pass
  rlist = []
  try:
   if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="":
    self.bus = digitemp.master.UART_Adapter(str(self.taskdevicepluginconfig[0]))
    rlist = digitemp.device.AddressableDevice(self.bus).get_connected_ROMs()
    self.plugin_init()
  except Exception as e:
   rlist = []
  self.readinprogress = 0
  return rlist

 def read_temperature(self):
   try:
    if self.bus.uart.is_open == False:
     self.plugin_init()
    return True, float(self.sensor.get_temperature())
   except Exception as e:
    pass
   return False, 0
