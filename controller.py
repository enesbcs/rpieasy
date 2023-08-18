#!/usr/bin/env python3
#############################################################################
########################## CONTROLLER skeleton ##############################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
class ControllerProto:
 CONTROLLER_ID = -1
 CONTROLLER_NAME = "Controller"

 def __init__(self,controllerindex):
  self.enabled = False
  self.controllerip="0.0.0.0"
  self.controllerport=80
  self.controlleruser=""
  self.controllerpassword=""
  self.initialized = False
  self.controllerid = self.CONTROLLER_ID
  self.controllerindex = controllerindex
  self.usesID = False
  self.connected = False
  self.onmsgcallbacksupported = False
  self.onmsgcallbackfunc = None
  self.usesAccount = False
  self.usesPassword = False
  self.usesMQTT = False
  self.timer30s = False
  self.backreport = False

 def getcontrollerid(self):
  return self.controllerid

 def getcontrollername(self):
  return self.CONTROLLER_NAME

 def getcontrollerindex(self):
  return self.controllerindex

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
   self.connect()
  self.initialized = True
  try:
   brtest = self.backreport
  except:
   self.backreport = False
  return True

 def connect(self):
  self.connected = True
  return True

 def disconnect(self):
  self.connected = False
  return True

 def isconnected(self):
  return self.connected

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1):
  return True

 def setonmsgcallback(self,callbackfunc):
  if self.onmsgcallbacksupported:
   self.onmsgcallbackfunc = callbackfunc # call onmsgcallbackfunc if controller able to send data to the plugin

 def controller_exit(self):
  self.disconnect()
 
 def webform_load(self): # create html page for settings
  return ""

 def webform_save(self,params): # process settings post reply
  return True

 def timer_thirty_second(self): # implement and set self.timer30s to true if you want to use
  return self.timer30s
