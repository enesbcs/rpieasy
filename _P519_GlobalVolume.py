#!/usr/bin/env python3
#############################################################################
################# System Sound volume helper for RPIEasy ####################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import Settings
import linux_os as OS

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 519
 PLUGIN_NAME = "Output - Global Sound Volume"
 PLUGIN_VALUENAME1 = "Volume"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SND
  self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.pullupoption = False
  self.inverselogicoption = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  if Settings.SoundSystem["usable"]==False:
   self.initialized = False
   self.enabled = False
  else:
   self.initialized = True
  self.sync(True)

 def webform_load(self):
  if Settings.SoundSystem["usable"]==False:
   webserver.addHtml("<tr><td><td><font color='red'>The sound system can not be used!</font>")
  return True

 def webform_save(self,params):
  self.sync()
  return True

 def sync(self,f=False):
  if self.enabled and self.initialized:
   v1 = OS.getvolume()
   if (int(v1) != int(self.uservar[0])) or (f):
      self.set_value(1,int(v1),True)

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized:
    try:
     val = int(value)
    except:
     val = -1
    if val>=0 and val<=100:
     OS.setvolume(val) # setvolt
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def plugin_receivedata(self,data):                        # set value based on mqtt input
  if (len(data)>0) and self.initialized and self.enabled:
   try:
    self.set_value(1,int(data[0]),False)
   except Exception as e:
    print("P519:",e)
#  print("Data received:",data) # DEBUG

