#!/usr/bin/env python3
#############################################################################
########### HDHK multi-channel AC current sensor plugin for RPIEasy #########
#############################################################################
#
# Plugin for the USB-RS485 HDHK device reading
#
# Copyright (C) 2022 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import lib.lib_hdhk as hdhk
import lib.lib_serial as rpiSerial

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 217
 PLUGIN_NAME = "Energy (AC) - HDHK modbus AC current sensor (TESTING)"
 PLUGIN_VALUENAME1 = "Amper"
 PLUGIN_VALUENAME2 = "Amper"
 PLUGIN_VALUENAME3 = "Amper"
 PLUGIN_VALUENAME4 = "Amper"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SER
  self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  self.valuecount = 4
  self.senddataoption = True
  self.recdataoption = False
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self.decimals = [2,2,2,2]
  self.hdhk = None
  self.readinprogress=0
  self.initialized=False

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = rpiSerial.serial_portlist()
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p217_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("Address of the USB-RS485 converter")
  else:
   webserver.addFormNote("No serial ports found")
  webserver.addFormNumericBox("Slave address","p217_saddr",self.taskdevicepluginconfig[1],1,32)

  webserver.addFormNote("Default address is 1.")
  if self.taskname=="":
   choice1 = 0
   choice2 = 1
   choice3 = 2
   choice4 = 3
   choice5 = 8
   channels = 16
  else:
   choice1 = self.taskdevicepluginconfig[2]
   choice2 = self.taskdevicepluginconfig[3]
   choice3 = self.taskdevicepluginconfig[4]
   choice4 = self.taskdevicepluginconfig[5]
   choice5 = self.taskdevicepluginconfig[6]
   channels = int(self.taskdevicepluginconfig[6])
  options = ["None"]
  optionvalues = [-1]
  for ch in range(0,channels):
    options.append(chr(65+ch))
    optionvalues.append(ch)
  webserver.addFormSelector("Channel1","plugin_217_ch0",len(options),options,optionvalues,None,choice1)
  webserver.addFormSelector("Channel2","plugin_217_ch1",len(options),options,optionvalues,None,choice2)
  webserver.addFormSelector("Channel3","plugin_217_ch2",len(options),options,optionvalues,None,choice3)
  webserver.addFormSelector("Channel4","plugin_217_ch3",len(options),options,optionvalues,None,choice4)
  options = ["8ch (28h-3Fh)","16ch (08h-17h)"]
  optionvalues = [8,16]
  webserver.addFormSelector("Number of channels on model","p217_mod",len(options),options,optionvalues,None,choice5)
  try:
    if self.hdhk != None and self.hdhk.initialized:
       webserver.addFormNote("HDHK product detected "+str(self.hdhk.prod))
  except:
    pass
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("p217_saddr",params)
  try:
   self.taskdevicepluginconfig[1] = int(par)
  except:
   self.taskdevicepluginconfig[1] = 1

  try:
   self.taskdevicepluginconfig[0] = str(webserver.arg("p217_addr",params)).strip()
   self.taskdevicepluginconfig[6] = int(webserver.arg("p217_mod",params))
   for v in range(0,4):
    par = webserver.arg("plugin_217_ch"+str(v),params)
    if par == "":
     par = -1
    else:
     par=int(par)
    if str(self.taskdevicepluginconfig[v+2])!=str(par):
     self.uservar[v] = 0
    self.taskdevicepluginconfig[v+2] = par
    if int(par)>0 and self.valuecount!=v+1:
     self.valuecount = (v+1)
   if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
   elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
   elif self.valuecount == 4:
    self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"webformload"+str(e))
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.taskdevicepluginconfig[0] = str(self.taskdevicepluginconfig[0]).strip()
  self.readinprogress=0
  self.initialized=False
  if self.valuecount == 1:
    self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  elif self.valuecount == 2:
    self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  elif self.valuecount == 3:
    self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
  elif self.valuecount == 4:
    self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
  if self.enabled and self.taskdevicepluginconfig[0]!="" and self.taskdevicepluginconfig[0]!="0":
   self.ports = str(self.taskdevicepluginconfig[0])+"/"+str(self.taskdevicepluginconfig[1])
   try:
    self.hdhk = hdhk.request_hdhk_device(self.taskdevicepluginconfig[0],self.taskdevicepluginconfig[1],int(self.taskdevicepluginconfig[6]))
    if self.hdhk != None and self.hdhk.initialized:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"HDHK " +self.hdhk.prod +" initialized at: "+str(self.taskdevicepluginconfig[0])+" / " +str(self.taskdevicepluginconfig[1]))
     self.initialized=True
     self.readinprogress = 0
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HDHK init failed at address "+str(self.taskdevicepluginconfig[1]))
   except Exception as e:
    self.hdhk = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HDHK init error: "+str(e))
  else:
   self.ports = ""

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   for v in range(0,4):
    vtype = int(self.taskdevicepluginconfig[v+2])
    if vtype != -1:
     try:
      c = 10
      while self.hdhk.busy and c>0:
       time.sleep(0.05)
       c=c-1
      value = self.hdhk.read_value(vtype)
     except:
      value = None
     if value != None:
      self.set_value(v+1,value,False)
   self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 
