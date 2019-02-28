#!/usr/bin/env python3
#############################################################################
####################### USB Temper plugin for RPIEasy #######################
#############################################################################
#
# Based on Pham Urwen's temper script
#  https://github.com/urwen/temper/
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import lib.lib_temper as utemper

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 508
 PLUGIN_NAME = "Environment - USB Temper"
 PLUGIN_VALUENAME1 = "Temperature"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_USB
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self.targetbus = -1
  self.targetdev = -1

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = False
  if enableplugin!=False:
   try:
    utemper.force_temper_detect()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Temper error: "+str(e))
  if str(self.taskdevicepluginconfig[0])=="0" or str(self.taskdevicepluginconfig[0]).strip()=="":
   self.targetbus = -1
   self.targetdev = -1
  elif len(utemper.get_temper_list())>0:
   if self.enabled or enableplugin:
    self.initialized = True
    self.targetbus = int(int(self.taskdevicepluginconfig[0]) / 10000)
    self.targetdev = int(self.taskdevicepluginconfig[0]) % 10000

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = utemper.get_select_list()
  if len(options)>0:
   webserver.addHtml("<tr><td>Device Address:<td>")
   webserver.addSelector_Head("p508_addr",True)
   for o in range(len(options)):
    webserver.addSelector_Item(str(options[o][1])+" "+str(options[o][2]),int(options[o][1]),(str(options[o][1])==str(choice1)),False)
   webserver.addSelector_Foot()
  webserver.addFormNote("Without root rights you will not see any Temper device!")
  return True

 def webform_save(self,params):
  par = webserver.arg("p508_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
  self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   try:
    suc = False
    rd = utemper.get_temper_list()
    if len(rd)>0:
     for t in range(len(rd)):
      if self.targetbus==int(rd[t]["busnum"]) and self.targetdev==int(rd[t]["devnum"]):
       temp = float(rd[t]['internal temperature'])
       self.set_value(1,temp,True)
       suc = True
       break
    if suc==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Temper read error!")
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Temper read error! "+str(e))
    self.enabled = False
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

