#!/usr/bin/env python3
#############################################################################
##################### Dallas DS18B20 plugin for RPIEasy #####################
#############################################################################
#
# Based on Linux kernel w1-gpio driver
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import glob

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 4
 PLUGIN_NAME = "Environment - DS18b20"
 PLUGIN_VALUENAME1 = "Temperature"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_W1
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if str(self.taskdevicepluginconfig[0])=="0" or str(self.taskdevicepluginconfig[0]).strip()=="":
   self.initialized = False
   if self.enabled and enableplugin:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Dallas device can not be initialized!")
  else:
   self.ports = str(self.taskdevicepluginconfig[0])
   self.initialized = True
   self.readinprogress = 0

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = self.find_dsb_devices()
  if len(options)>0:
   webserver.addHtml("<tr><td>Device Address:<td>")
   webserver.addSelector_Head("p004_addr",True)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
  webserver.addFormNote("You have to setup one pin (at least) for <b>1WIRE</b> type at <a href='pinout'>pinout settings page</a> before use!")
  return True

 def webform_save(self,params):
  par = webserver.arg("p004_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
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

 def find_dsb_devices(self):
  rlist = []
  try:
   devlist = glob.glob('/sys/bus/w1/devices/*')
   if len(devlist)>0:
    for d in devlist:
     td = d.split("/")
     tdname = td[len(td)-1]
     if "-" in tdname:
      tf = tdname.split("-")[0].lower()
      if tf in ["10","22","28","3b","42"]:
       rlist.append(tdname)
   else:
    rlist = []
  except:
   rlist = []
  return rlist

 def read_temperature(self):
   lines = []
   try:
    with open('/sys/bus/w1/devices/' + str(self.taskdevicepluginconfig[0]) +'/w1_slave') as f:
        lines = f.readlines()
    if len(lines) != 2:
        return False, 0
    if 'YES' not in lines[0]:
        return False, 0
    d = lines[1].strip().split('=')
    if len(d) != 2:
        return False, 0
   except:
    return False, 0
   return True, float(d[1])/1000.0
