#!/usr/bin/env python3
#############################################################################
################## Generic UDP controller for RPIEasy #######################
#############################################################################
#
# Generic UDP controller
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import misc
import rpieGlobals
import time
import webserver
import Settings
import socket
import threading
import commands

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 10
 CONTROLLER_NAME = "Generic UDP"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.onmsgcallbacksupported = False # use direct set_value() instead of generic callback to make sure that values setted anyway
  self.controllerport = 514
  self.inchannel = "%sysname%_%tskname%_%valname%=%value%"
  self.templatestr = ""

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.templatestr, state = commands.parseruleline(self.inchannel) # replace global variables
  self.templatestr = self.templatestr.replace("==","=")
  self.initialized = True
  return True

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Report template","inchannel",self.inchannel,255)
  return True

 def webform_save(self,params): # process settings post reply
  self.inchannel = webserver.arg("inchannel",params)
  return True

 def udpsender(self,data):
   try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if str(self.controllerip).endswith(".255"):
     s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if type(data) is bytes:
     dsend = data
    elif type(data) is str:
     dsend = bytes(data,"utf-8")
    else:
     dsend = bytes(data)
    s.sendto(dsend, (self.controllerip,int(self.controllerport)))
#    print(self.controllerip,self.controllerport,dsend) # DEBUG
   except Exception as e:
    print(e)

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if tasknum is None:
   return False
  if tasknum!=-1 and self.enabled:
   if tasknum<len(Settings.Tasks):
    if Settings.Tasks[tasknum] != False:
      templatestra = self.templatestr.replace('%tskname%',Settings.Tasks[tasknum].gettaskname())
      procarr = []
      for u in range(Settings.Tasks[tasknum].valuecount):
       vn = str(Settings.Tasks[tasknum].valuenames[u]).strip()
       if vn!="":
        templatestr = templatestra.replace('%valname%',vn)
        templatestr = templatestr.replace('%value%',str(Settings.Tasks[tasknum].uservar[u]))
        t = threading.Thread(target=self.udpsender, args=(templatestr,))
        t.daemon = True
        procarr.append(t)
        t.start()
      if len(procarr)>0:
       for process in procarr:
        process.join()
