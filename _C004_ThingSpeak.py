#!/usr/bin/env python3
#############################################################################
################### ThingSpeak Controller for RPIEasy #######################
#############################################################################
#
# Only one way data sending supported for obvious reasons.
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
import Settings
import misc
import urllib.request
import threading
import base64
import webserver
from urllib import request, parse
import time
import rpieTime

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 4
 CONTROLLER_NAME = "ThingSpeak"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = True
  self.usesPassword = True
  self.controllerport = 80
  self.controllerip = "api.thingspeak.com"
  self.defaultdelay = 15 # 15 seconds between two sending
  self.lastsend = 0

 def webform_load(self):
  webserver.addFormNote("Add your ThingSpeak Channel ID as Username, and Write API Key as Password")
  webserver.addFormNote("Name your values from field1..field8 to use multiple field in the Channel, or name it as you wish if you are using only one Device")
  return True

 def controller_init(self,enablecontroller=None):
  if enablecontroller!=None:
   self.enabled = enablecontroller
  self.initialized = False
  if self.controllerpassword!="" and self.controllerip!="" and self.controllerip!="0.0.0.0":
   self.initialized = True
  return self.initialized

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if tasknum is None:
   return False
  if self.enabled and self.initialized:
    if tasknum!=-1:
     if time.time()-self.lastsend<self.defaultdelay:
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sending too soon for ThingSpeak, skip")
      rpieTime.addsystemtimer(3,self.retransmit,[tasknum,0])
      return False
     jdata = {}
     jdata['key'] = self.controllerpassword
     if changedvalue==-1:
      for u in range(Settings.Tasks[tasknum].valuecount):
       vname = Settings.Tasks[tasknum].valuenames[u].strip().lower()
       if vname.startswith('field')==False:
        vname = "field"+str(u+1)
       jdata[vname] = str(value[u])
     else:
      u = changedvalue-1
      vname = Settings.Tasks[tasknum].valuenames[u].strip().lower()
      if vname.startswith('field')==False:
        vname = "field"+str(u+1)
      jdata[vname] = str(value[u])

     jdata = urllib.parse.urlencode(jdata).encode("utf-8")
     urlstr = "http://"+str(self.controllerip)+":"+str(self.controllerport)+"/update" # create destination url
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sending task "+str(tasknum+1)+" data to ThingSpeak at "+str(urlstr))
     self.lastsend = time.time()
     httpproc = threading.Thread(target=self.urlpost, args=(urlstr,jdata,))  # use threading to avoid blocking
     httpproc.daemon = True
     httpproc.start()
     return True
  return False

 def urlpost(self,url,postdata):
  try:
   hdr = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
   req = request.Request(url, data=postdata,headers=hdr)
   response = request.urlopen(req)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.controllerip+" connection failed "+str(e))

 def retransmit(self,timerid,pararray):
   tasknum = int(pararray[0])
   Settings.Tasks[tasknum]._lastdataservetime = 0 # make it try again
