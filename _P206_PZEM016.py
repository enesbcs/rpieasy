#!/usr/bin/env python3
#############################################################################
####################### PZEM016 plugin for RPIEasy ##########################
#############################################################################
#
# Plugin for the USB-RS485 PZEM-016 device reading
#
# Available commands:
#  PZEMADDRESS,<currentaddress>,<newaddress>   	- change address of pzem device
#  PZEMRESET,<address>			 	- PZEM reset energy at address
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import lib.lib_pzem as uPZEM
import lib.lib_serial as rpiSerial

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 206
 PLUGIN_NAME = "Energy (AC) - PZEM016 USB (TESTING)"
 PLUGIN_VALUENAME1 = "Volt"
 PLUGIN_VALUENAME2 = "Amper"
 PLUGIN_VALUENAME3 = "Watt"
 PLUGIN_VALUENAME4 = "Wh"

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
  self.pzem = None
  self.readinprogress=0
  self.initialized=False

 def webform_load(self): # create html page for settings
  choice1 = self.stripstring(self.taskdevicepluginconfig[0])
  options = rpiSerial.serial_portlist()
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p206_addr",False)
   for o in range(len(options)):
    options[o] = self.stripstring(options[o])
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
   webserver.addFormNote("Address of the USB-RS485 converter")
  else:
   webserver.addFormNote("No serial ports found")
  webserver.addFormNumericBox("Slave address","p206_saddr",self.taskdevicepluginconfig[1],1,248)

  webserver.addFormNote("Default address is 1. Use 'pzemaddress,[currentaddress],[newaddress]' command to change it. (broadcast=248)")
  if self.taskname=="":
   choice1 = 0
   choice2 = 1
   choice3 = 3
   choice4 = 5
  else:
   choice1 = self.taskdevicepluginconfig[2]
   choice2 = self.taskdevicepluginconfig[3]
   choice3 = self.taskdevicepluginconfig[4]
   choice4 = self.taskdevicepluginconfig[5]
  options = ["None", "Volt","Amper","Watt", "Wh","Hz","PwrFact"]
  optionvalues = [-1, 0, 1, 3, 5, 7, 8]
  webserver.addFormSelector("Indicator1","plugin_206_ind0",len(options),options,optionvalues,None,choice1)
  webserver.addFormSelector("Indicator2","plugin_206_ind1",len(options),options,optionvalues,None,choice2)
  webserver.addFormSelector("Indicator3","plugin_206_ind2",len(options),options,optionvalues,None,choice3)
  webserver.addFormSelector("Indicator4","plugin_206_ind3",len(options),options,optionvalues,None,choice4)
  webserver.addFormCheckBox("Increase timeout for slow PZEM004 compatibility","plugin_206_slow",self.taskdevicepluginconfig[6])
  return True

 def webform_save(self,params): # process settings post reply
  paddr = self.taskdevicepluginconfig[1]
  ninit = False
  par = webserver.arg("p206_saddr",params)
  try:
   self.taskdevicepluginconfig[1] = int(par)
  except:
   self.taskdevicepluginconfig[1] = 1
  try:
   if int(paddr) != int(self.taskdevicepluginconfig[1]):
    ninit = True
  except:
   ninit = True
  self.taskdevicepluginconfig[6] = (webserver.arg("plugin_206_slow",params)=="on")
  try:
   self.taskdevicepluginconfig[0] = self.stripstring(webserver.arg("p206_addr",params))
   for v in range(0,4):
    par = webserver.arg("plugin_206_ind"+str(v),params)
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
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,+str(e))
  if ninit:
   self.plugin_init()
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.taskdevicepluginconfig[0] = self.stripstring(self.taskdevicepluginconfig[0])
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
   if self.taskdevicepluginconfig[6]:
    timeout = 3
    if self.interval<3:
     self.interval=3 # sorry, use better device if you need smaller intervals
   else:
    timeout = 0.1
   try:
    self.pzem = uPZEM.request_pzem_device(self.taskdevicepluginconfig[0],self.taskdevicepluginconfig[1],timeout)
    if self.pzem != None and self.pzem.initialized:
     if timeout>1:
      sl = "slow "
     else:
      sl = ""
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"PZEM "+sl+"initialized at: "+str(self.taskdevicepluginconfig[0])+" / " +str(self.taskdevicepluginconfig[1]))
     self.initialized=True
     self.readinprogress = 0
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PZEM init failed at address "+str(self.taskdevicepluginconfig[1]))
   except Exception as e:
    self.pzem = None
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PZEM init error: "+str(e))
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
      while self.pzem.busy and c>0:
       time.sleep(0.05)
       c=c-1
      value = self.pzem.read_value(vtype)
     except:
      value = None
     if value != None:
      self.set_value(v+1,value,False)
   self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0][:4] != "pzem":
   return False
  if cmdarr[0] == "pzemaddress":
      try:
       ca = int(cmdarr[1].strip())
       na = int(cmdarr[2].strip())
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      tpzem = uPZEM.request_pzem_device(self.taskdevicepluginconfig[0],ca)
      if tpzem:
       res = tpzem.changeAddress(na)
      else:
       res = False
  elif cmdarr[0] == "pzemreset":
      try:
       ca = int(cmdarr[1].strip())
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      tpzem = uPZEM.request_pzem_device(self.taskdevicepluginconfig[0],ca)
      if tpzem:
       res = tpzem.resetenergy()
      else:
       res = False
  return res

 def stripstring(self,tstr):
   sentence = str(tstr)
   sentence = ''.join(sentence.split())
   return sentence
