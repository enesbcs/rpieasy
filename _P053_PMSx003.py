#!/usr/bin/env python3
#############################################################################
####################### PMSx003 plugin for RPIEasy ##########################
#############################################################################
#
# Particle sensor plugin based on PyPMS
#
# Thank you for the test device to Zoltan Nagy!
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import lib.lib_serial as rpiSerial
import lib.lib_pms as rpiPMS

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 53
 PLUGIN_NAME = "Dust - PMSx003/SDS01x/SPS30 (TESTING)"
 PLUGIN_VALUENAME1 = "Value1"
 PLUGIN_VALUENAME2 = "Value2"
 PLUGIN_VALUENAME3 = "Value3"
 PLUGIN_VALUENAME4 = "Value4"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SER
   self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
   self.readinprogress = 0
   self.valuecount = 4
   self.senddataoption = True
   self.timeroption = True
   self.timeroptional = False
   self.formulaoption = True
   self.initialized = False
   self.reader = None
   self._header = []

 def plugin_exit(self):
   self.initialized = False
   try:
     self.reader.disconnect()
   except:
     pass

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.readinprogress = 0
  self.initialized = False
  try:
   if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="":
    if self.enabled:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Try to init serial "+str(self.taskdevicepluginconfig[0]))
     try:
      self.reader = rpiPMS.request_pms_device(str(self.taskdevicepluginconfig[5]), str(self.taskdevicepluginconfig[0]))
#      self.reader.connect()
      self._header = []
      self.initialized = True
     except:
      pass
     if self.initialized:
      pn = self.taskdevicepluginconfig[0].split("/")
      self.ports = str(pn[-1])
    else:
     self.ports = 0
  except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PMS init error "+str(e))

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = rpiSerial.serial_portlist()
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p053_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("For RPI use 'raspi-config' tool: 5- Interfacing Options-P6 Serial- (Kernel logging disabled + serial port hardware enabled) before enable this plugin")
  else:
   webserver.addFormNote("No serial ports found")
  sensortypes = ["PMSx003","PMS3003","PMS5003S","PMS5003ST","PMS5003T","SDS01x","SDS198","HPMA115S0","HPMA115C0","SPS30","MCU680"]
  webserver.addHtml("<tr><td>Sensor type:<td>")
  webserver.addSelector_Head("p053_sensor",False)
  for o in range(len(sensortypes)):
    webserver.addSelector_Item(sensortypes[o],sensortypes[o],(str(sensortypes[o])==str(self.taskdevicepluginconfig[5])),False)
  webserver.addSelector_Foot()
  options = ["None","PM01","PM25", "PM04","PM10","PM100","Temperature","Relative humidity"]
  optionvalues = ["None","pm01","pm25","pm04","pm10","pm100","temp","rhum"]
  for os in range(1,5):
   webserver.addHtml("<tr><td>Value"+str(os)+":<td>")
   webserver.addSelector_Head("p053_ind"+str(os),False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],optionvalues[o],(str(optionvalues[o])==str(self.taskdevicepluginconfig[os])),False)
   webserver.addSelector_Foot()
  return True

 def webform_save(self,params):
  par = webserver.arg("p053_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
  par = webserver.arg("p053_sensor",params)
  self.taskdevicepluginconfig[5] = str(par)
  for v in range(1,5):
   par = webserver.arg("p053_ind"+str(v),params)
   if par == "":
    par = "None"
   if str(self.taskdevicepluginconfig[v])!=str(par):
    self.uservar[v-1] = 0
   self.taskdevicepluginconfig[v] = str(par)
   if str(par)!="None":
    self.valuecount = v
  if self.valuecount == 1:
   self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  elif self.valuecount == 2:
   self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  elif self.valuecount == 3:
   self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  elif self.valuecount == 4:
   self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  self.plugin_init()
  return True

 def plugin_read(self):
  result = False
  if self.initialized==False or self.enabled==False:
   return False
  if self.reader.connected==False:
   self.reader.connect()
  if self.readinprogress==0:
   self.readinprogress = 1
   noread = True
   i = 12
   obs = []
   values = []
   while noread and i>0:
    i-=0.1
    if self.reader.is_open:
     i-=1
     try:
#      buffer = self.reader.pms._cmd("passive_read")
#      obs = self.reader.pms.sensor.decode(buffer)
      obs = self.reader.readdata()
      noread = (obs is None)
      try:
       if len(self._header) < 1:
        h = obs.__format__("header")
        self._header = h.split(",")
      except:
       pass
#      print(obs,noread)#debug
      values = obs.__format__("csv").split(",")
     except Exception as e:
      time.sleep(0.1)
    else:
     time.sleep(0.1)
   if noread==False:
    if len(self._header)>0 and len(values)>0:
     self.set_value(1,self.getvalue(values,self.taskdevicepluginconfig[1]),False)
     if self.valuecount>1:
      self.set_value(2,self.getvalue(values,self.taskdevicepluginconfig[2]),False)
      if self.valuecount>2:
       self.set_value(3,self.getvalue(values,self.taskdevicepluginconfig[3]),False)
       if self.valuecount>3:
        self.set_value(4,self.getvalue(values,self.taskdevicepluginconfig[4]),False)
     self.plugin_senddata()
   else:
    self.reader.connect(True)
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def getvalue(self,valuelist,valuename):
   res = 0
   if len(self._header) > 0:
    vptr = -1
    for i in range(0,len(self._header)):
     try:
      if self._header[i].strip().lower() == valuename.strip().lower():
        vptr = i
        break
     except:
      pass
    if vptr>-1 and vptr<len(valuelist):
     res = valuelist[vptr]
   return res

