#!/usr/bin/env python3
#############################################################################
################### Thingsboard HTTP Controller for RPIEasy #################
#############################################################################
#
# Only one way data sending supported.
#
# Copyright (C) 2023 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
import Settings
import misc
import threading
import webserver
from urllib import request, parse
import ssl
import json

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 26
 CONTROLLER_NAME = "Thingsboard HTTP"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = False
  self.usesPassword = True # URL key
  self.controllerport = 443
  self.controllerip = "demo.thingsboard.io"

 def webform_load(self):
  webserver.addFormNote("Add your generated Thingsboard device ACCESS_TOKEN as Password")
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
     if Settings.Tasks[tasknum] and Settings.Tasks[tasknum].enabled:
      if Settings.Tasks[tasknum].recdataoption==False or (Settings.Tasks[tasknum].vtype not in [rpieGlobals.SENSOR_TYPE_SWITCH, rpieGlobals.SENSOR_TYPE_DIMMER]):
       tname = Settings.Tasks[tasknum].gettaskname()
       jdata = {}
       for u in range(Settings.Tasks[tasknum].valuecount):
           jdata[tname + "-"+ Settings.Tasks[tasknum].valuenames[u]] = value[u]
       try:
           usebattery = float(str(usebattery).strip())
       except Exception as e:
           usebattery = -1
       bval = -1
       if usebattery != -1 and usebattery != 255:
           bval = usebattery
       else:
           bval = misc.get_battery_value()
       if bval != -1 and bval != 255:
           jdata["'"+ tname + "-battery'"] = bval
       if userssi != -1:
           jdata["'"+ tname + "-rssi'"] = userssi

       urlstr = "http"
       if self.controllerport != 80:
        urlstr += "s"
       urlstr += "://"+str(self.controllerip)+":"+str(self.controllerport)+"/api/v1/"+str(self.controllerpassword)+"/telemetry"
       misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sending task "+str(tasknum+1)+" data to Thingsboard at "+str(urlstr))
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
   hdr = {'Content-type': 'application/json'}
   sdata = json.dumps(postdata)
   sdata = sdata.encode()
   req = request.Request(url, data=sdata, headers=hdr)
   response = request.urlopen(req,None,2,context=ctx)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.controllerip+" connection failed "+str(e))
