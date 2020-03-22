#!/usr/bin/env python3
#############################################################################
######################## Ping plugin for RPIEasy ############################
#############################################################################
#
# Ping plugin for testing availability of a remote TCP/IP station.
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import misc
import rpieTime
from ping3 import ping # sudo pip3 install ping3

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 126
 PLUGIN_NAME = "Network - Ping"
 PLUGIN_VALUENAME1 = "State"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  if self.enabled:
   self.set_value(1,1,False) # init with 1
   self.initialized = True
   self.readinprogress = 0
   try:
    if self.taskdevicepluginconfig[1]<=0:
     self.taskdevicepluginconfig[1] = 0.1
   except:
     self.taskdevicepluginconfig[1] = 0.1

 def webform_load(self):
  webserver.addFormTextBox("Remote station address","plugin_126_addr",str(self.taskdevicepluginconfig[0]),128)
  webserver.addFormFloatNumberBox("Timeout","plugin_126_timeout",float(self.taskdevicepluginconfig[1]),0,20)
  webserver.addUnit("s")
  webserver.addFormNote("Ping3 icmp will only work with ROOT rights!")
  return True

 def webform_save(self,params):
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_126_addr",params)).strip()
  if str(self.taskdevicepluginconfig[0])=="0":
   self.taskdevicepluginconfig[0]=""
  try:
   self.taskdevicepluginconfig[1] = float(webserver.arg("plugin_126_timeout",params))
   if self.taskdevicepluginconfig[1]<=0:
    self.taskdevicepluginconfig[1] = 0.1
  except:
   self.taskdevicepluginconfig[1] = 0.1
  return True

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled and self.readinprogress==0:
   self.readinprogress = 1
   try:
    reply = ping(self.taskdevicepluginconfig[0],timeout=self.taskdevicepluginconfig[1],unit="ms")
   except Exception as e:
    reply = None
#    print(e)
   if reply is None or reply == False: # second try
    try:
     reply = ping(self.taskdevicepluginconfig[0],timeout=self.taskdevicepluginconfig[1]*2,unit="ms")
    except Exception as e:
     reply = None
#     print(e)
   if reply is None or reply == False:
    res = 0
   else:
    res = 1
#   print(reply,res)
   self.set_value(1,res,True)
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result
