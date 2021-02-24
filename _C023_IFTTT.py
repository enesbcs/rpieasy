#!/usr/bin/env python3
#############################################################################
###################### IFTTT Controller for RPIEasy #########################
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
import ssl

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 23
 CONTROLLER_NAME = "IFTTT Webhooks"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = False
  self.usesPassword = True # URL key
  self.controllerport = 443
  self.controllerip = "maker.ifttt.com"

 def webform_load(self):
  webserver.addFormNote("Add your IFTTT Webhook URL key as Password")
  webserver.addFormNote("Name your values from value1..value3 to use multiple field in the Channel, or name it as you wish if you are using only one Device. The event name will be the device name.")
  return True

 def controller_init(self,enablecontroller=None):
  if enablecontroller!=None:
   self.enabled = enablecontroller
  self.initialized = False
  if self.controllerpassword!="" and self.controllerip!="" and self.controllerip!="0.0.0.0":
   self.initialized = True
  return self.initialized
 
 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled and self.initialized and tasknum is not None:
    if tasknum!=-1:
     jdata = {}
     jdata['key'] = self.controllerpassword
     if changedvalue==-1:
      for u in range(Settings.Tasks[tasknum].valuecount):
       vname = Settings.Tasks[tasknum].valuenames[u].strip().lower()
       if vname.startswith('value')==False:
        vname = "value"+str(u+1)
       jdata[vname] = str(value[u])
       if u>2:
        break
     else:
      u = changedvalue-1
      if u<3:
       vname = Settings.Tasks[tasknum].valuenames[u].strip().lower()
       if vname.startswith('value')==False:
        vname = "value"+str(u+1)
       jdata[vname] = str(value[u])

     jdata = urllib.parse.urlencode(jdata).encode("utf-8")
     urlstr = "https://"+str(self.controllerip)+":"+str(self.controllerport)+"/trigger/"+str(Settings.Tasks[tasknum].gettaskname())+"/with/key/" # create destination url
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sending task "+str(tasknum+1)+" data to IFTTT at "+str(urlstr))
     urlstr += str(self.controllerpassword) # create destination url
     httpproc = threading.Thread(target=self.urlpost, args=(urlstr,jdata,))  # use threading to avoid blocking
     httpproc.daemon = True
     httpproc.start()
     return True
  return False

 def urlpost(self,url,postdata):
  try:
   ctx = ssl.create_default_context()
   ctx.check_hostname=False
   ctx.verify_mode = ssl.CERT_NONE
   hdr = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
   req = request.Request(url, data=postdata, headers=hdr)
   response = request.urlopen(req,None,2,context=ctx)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.controllerip+" connection failed "+str(e))

