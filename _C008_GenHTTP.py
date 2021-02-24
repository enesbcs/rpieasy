#!/usr/bin/env python3
#############################################################################
################## Generic HTTP Controller for RPIEasy ######################
#############################################################################
#
# Only one way data sending supported for obvious reasons.
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
import misc
import urllib.request
import urllib.parse
import threading
import webserver
import Settings
import commands

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 8
 CONTROLLER_NAME = "Generic HTTP"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = False
  self.usesPassword = False
  self.controllerport = 80
  self.inchannel = "demo.php?name=%sysname%&task=%tskname%&taskid=%id%&valuename=%valname%&value=%value%"
  self.templatestr = ""

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.templatestr, state = commands.parseruleline(self.inchannel) # replace global variables
  self.templatestr = self.templatestr.replace("==","=")
  self.initialized = True
  return True

 def webform_load(self):
  webserver.addFormTextBox("Report template","inchannel",self.inchannel,255)
  return True

 def webform_save(self,params): # process settings post reply
  self.inchannel = webserver.arg("inchannel",params)
  return True

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if tasknum is None:
   return False
  if tasknum!=-1 and self.enabled:
   if tasknum<len(Settings.Tasks):
    if Settings.Tasks[tasknum] != False:
     procarr = []
     try:
      hn = str(urllib.parse.quote(str(Settings.Tasks[tasknum].gettaskname())))
      templatestra = self.templatestr.replace('%tskname%',hn)
      templatestra = templatestra.replace('%id%',str(tasknum+1))
      for u in range(Settings.Tasks[tasknum].valuecount):
       vn = str(Settings.Tasks[tasknum].valuenames[u]).strip()
       if vn!="":
        vn = str(urllib.parse.quote(vn))
        templatestr = templatestra.replace('%valname%',vn)
        val = str(urllib.parse.quote(str(Settings.Tasks[tasknum].uservar[u])))
        templatestr = templatestr.replace('%value%',val)
        urlstr = "http://"+str(self.controllerip)+":"+str(self.controllerport)+"/"+templatestr
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,urlstr) # sendviahttp
        t = threading.Thread(target=self.urlget, args=(urlstr,))  # use threading to avoid blocking
        t.daemon = True
        procarr.append(t)
        t.start()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,e)
     if len(procarr)>0:
       for process in procarr:
        process.join()

 def urlget(self,url):
  try:
   content = urllib.request.urlopen(url,None,2)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.controllerip+" connection failed "+str(e))
