#!/usr/bin/env python3
#############################################################################
############### Domoticz HTTP/HTTPS Controller for RPIEasy ##################
#############################################################################
#
# Only one way data sending supported for obvious reasons.
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
from helper_domoticz import *
import misc
import urllib.request
from multiprocessing import Process
import base64
import webserver

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 1
 CONTROLLER_NAME = "Domoticz HTTP"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = True
  self.usesAccount = True
  self.usesPassword = True
  self.authmode = 0
  
 def webform_load(self):
  try:
   am = self.authmode
  except:
   am = 0
  options = ["HTTP","HTTPS/auto negotiation","HTTPS/disable verify"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Mode","c001_mode",len(optionvalues),options,optionvalues,None,int(am))
  return True
  
 def webform_save(self,params):
  try:
   self.authmode = int(webserver.arg("c001_mode",params))
  except:
   self.authmode = 0
  return True

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled:
   if int(idx) != 0:
    try:
     usebattery = float(usebattery)
    except:
     usebattery = -1
    if int(sensortype)==rpieGlobals.SENSOR_TYPE_SWITCH:
      url = "/json.htm?type=command&param=switchlight&idx="
      url += str(idx)
      url += "&switchcmd="
      if round(float(value[0])) == 0:
         url += "Off"
      else:
         url += "On"
    elif int(sensortype)==rpieGlobals.SENSOR_TYPE_DIMMER:
      url = "/json.htm?type=command&param=switchlight&idx="
      url += str(idx)
      url += "&switchcmd="
      if float(value[0]) == 0:
       url += "Off"
      else:
       url += "Set%20Level&level="
       url += str(value[0])
    else:
     url = "/json.htm?type=command&param=udevice&idx="
     url += str(idx)
     url += "&nvalue=0&svalue="
     url += formatDomoticzSensorType(sensortype,value)
    url += "&rssi="
    url += mapRSSItoDomoticz(userssi)
    if int(usebattery) != -1 and int(usebattery) != 255: # battery input 0..100%, 255 means not supported
     url += "&battery="
     url += str(int(usebattery))
    else:
     bval = misc.get_battery_value()
     url += "&battery="
     url += str(int(bval))
    urlstr = self.controllerip+":"+self.controllerport+url+self.getaccountstr()
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,urlstr) # sendviahttp
    httpproc = Process(target=self.urlget, args=(urlstr,))  # use multiprocess to avoid blocking
    httpproc.start()
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT : IDX cannot be zero!")

 def urlget(self,url):
  try:
     am = self.authmode
  except:
     am = 0
  if am==0:         # http
     url = "http://"+str(url)
  elif am==1 or am==2: # https
     url = "https://"+str(url)
     try:
      import ssl
     except:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OpenSSL is not reachable!")
      #self.authmode=0
      return False
     if am==2: # https insecure
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
     else:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
  try:
   if am == 0:
    content = urllib.request.urlopen(url,None,2)
   else:
    content = urllib.request.urlopen(url,None,2, context=ctx)
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Controller: "+self.controllerip+" connection failed "+str(e))

 def getaccountstr(self):
  retstr = ""
  if self.controlleruser!="" or self.controllerpassword!="":
    acc = base64.b64encode(bytes(self.controlleruser,"utf-8")).decode("utf-8")
    pw =  base64.b64encode(bytes(self.controllerpassword,"utf-8")).decode("utf-8")
    retstr = "&username="+ str(acc) +"&password="+ str(pw)
  return retstr
