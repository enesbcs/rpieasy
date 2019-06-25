#!/usr/bin/env python3
#############################################################################
################### Notification plugin skeleton ############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

class NPluginProto: # Skeleton for every notification plugin! Override necessary functions and extend as neeeded!
 NPLUGIN_ID = -1
 NPLUGIN_NAME = "Notifier"

 def __init__(self,nindex): # general init
  self.number = self.NPLUGIN_ID
  self.usesMessaging = True
  self.usesGPIO=0
  self.enabled = False
  self.nindex = nindex
  self.initialized = False

 def getnpluginid(self):
  return self.number

 def getdevicename(self):
  return self.NPLUGIN_NAME

 def getuniquename(self):
  return self.NPLUGIN_NAME

 def webform_load(self): # create html page for settings
  return ""

 def webform_save(self,params): # process settings post reply
  return True

 def plugin_init(self,enableplugin=None): # init plugin when startup, load settings if available
  if enableplugin != None:
   self.enabled = enableplugin
  if self.enabled:
   if self.initialized == False:
    self.initialized = True
  return True

 def plugin_exit(self): # deinit plugin, save settings?
  if self.initialized:
   self.initialized = False
  return True

 def notify(self,pmsg=""):
  result = False
  return result
