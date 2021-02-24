#!/usr/bin/env python3
#############################################################################
################### FHEM HTTP Controller for RPIEasy ########################
#############################################################################
#
# Only one way data sending supported for obvious reasons.
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
import Settings
import os_os as OS
import misc
import urllib.request
import threading
import base64
import webserver
from urllib import request, parse
import json
import time

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 9
 CONTROLLER_NAME = "FHEM HTTP"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = True
  self.usesPassword = True
  self.controllerport = 8383
  self.ip = ""
  self.iptime = 0

 def getIP(self):
  if time.time()-self.iptime>30:
   self.iptime=time.time()
   ip = ""
   try:
     defdev = Settings.NetMan.getprimarydevice()
   except:
     defdev = -1
   if defdev != -1:
     ip = Settings.NetworkDevices[defdev].ip
   else:
     ip = ""
   if ip == "":
     ip = str(OS.get_ip())
   if ip != "":
    self.ip = ip
  return self.ip

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if tasknum is None:
   return False
  if self.enabled:
    if tasknum!=-1:
     jdata = {}
     jdata['module'] = "ESPEasy" # or similar...
     jdata['version'] = "1.04"
     jdata["data"] = {}
     jdata["data"]["ESP"] = {}
     jdata["data"]["ESP"]["name"] = str(Settings.Settings["Name"])
     jdata["data"]["ESP"]["unit"] = int(Settings.Settings["Unit"])
     jdata["data"]["ESP"]['version'] = 2 # or similar...
     jdata["data"]["ESP"]['build'] = int(rpieGlobals.BUILD)
     jdata["data"]["ESP"]['build_notes'] = "RPIEasy"
     jdata["data"]["ESP"]['build_git'] = ""
     jdata["data"]["ESP"]['node_type_id'] = int(rpieGlobals.NODE_TYPE_ID)
     jdata["data"]["ESP"]['sleep'] = 0
     jdata["data"]["ESP"]['ip'] = str(self.getIP())
     jdata["data"]["SENSOR"] = {}
     tname = Settings.Tasks[tasknum].gettaskname()
     if changedvalue==-1:
      for u in range(Settings.Tasks[tasknum].valuecount):
       vname = Settings.Tasks[tasknum].valuenames[u]
       if vname != "":
        gval = str(value[u])
        if gval == "":
         gval = "0"
        fid = str(u)
        jdata["data"]["SENSOR"][fid] = {}
        jdata["data"]["SENSOR"][fid]["deviceName"] = Settings.Tasks[tasknum].gettaskname()
        jdata["data"]["SENSOR"][fid]["valueName"] = vname
        jdata["data"]["SENSOR"][fid]["type"] = int(sensortype)
        jdata["data"]["SENSOR"][fid]["value"] = str(gval)
     else:
      vname = Settings.Tasks[tasknum].valuenames[changedvalue-1]
      if vname != "":
       gval = str(value[changedvalue-1])
       if gval == "":
         gval = "0"
       fid = str(changedvalue-1)
       jdata["data"]["SENSOR"][fid] = {}
       jdata["data"]["SENSOR"][fid]["deviceName"] = Settings.Tasks[tasknum].gettaskname()
       jdata["data"]["SENSOR"][fid]["valueName"] = vname
       jdata["data"]["SENSOR"][fid]["type"] = int(sensortype)
       jdata["data"]["SENSOR"][fid]["value"] = str(gval)

     jdata = json.dumps(jdata,separators=(',', ':')).encode('utf8') # encode data to proper json string
     urlstr = "http://"+str(self.controllerip)+":"+self.controllerport+"/ESPEasy" # create destination url
#     print(urlstr)
#     print(jdata)
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sending task "+str(tasknum+1)+" data to FHEM at "+str(urlstr))
     httpproc = threading.Thread(target=self.urlpost, args=(urlstr,jdata,))  # use threading to avoid blocking
     httpproc.daemon = True
     httpproc.start()

 def urlpost(self,url,postdata):
  try:
   if self.controlleruser!="" or self.controllerpassword!="":
    base64string = base64.b64encode( bytes((self.controlleruser+":"+self.controllerpassword),"utf-8") )
    hdr = {'Authorization' : 'Basic '+ str(base64string.decode())}
   else:
    hdr = {}
   req = request.Request(url, data=postdata,headers=hdr) #,headers={'content-type': 'application/json'})
   response = request.urlopen(req)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.controllerip+" connection failed "+str(e))
