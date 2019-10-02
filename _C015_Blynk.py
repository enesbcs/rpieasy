#!/usr/bin/env python3
#############################################################################
##################### Blynk Controller for RPIEasy ##########################
#############################################################################
#
# Two way data sending supported
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
import Settings
import misc
import webserver
import time
import threading
import lib.lib_blynk as BLYNK
import blynklib

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 15
 CONTROLLER_NAME = "Blynk"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.onmsgcallbacksupported = True
  self.usesAccount = False
  self.usesPassword = True # add Token!
  self.controllerport = 80
  self.ip = ""
  self.iptime = 0
  self.bgproc = None
  self.controllerip = ""

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.initialized = False
  if self.controllerpassword!="":
   if self.enabled:
     if str(self.controllerip).strip() == "":
      baddr = "blynk-cloud.com"
     else:
      baddr = str(self.controllerip)
     self.enabled = False
     try:
      BLYNK.blynk.disconnect()
      BLYNK.blynk = None
     except Exception as e:
      print(e)
     try:
      BLYNK.blynk = blynklib.Blynk(self.controllerpassword,server=baddr,port=int(self.controllerport),heartbeat=15)
      BLYNK.addhandler(self.on_message)
      BLYNK.blynk.connect()
      self.enabled = True
      self.initialized = True
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Blynk error: "+str(e))
      self.initialized = False
     try:
      self.bgproc = threading.Thread(target=BLYNK.BlynkLoop)
      self.bgproc.daemon = True
      self.bgproc.start()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Blynk threading error: "+str(e))
  else:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Blynk error: Token missing")
  return True

 def webform_load(self):
  webserver.addFormNote("Add your Blynk token to the Password field! Only one Blynk can be used on one system!")
  return True

 def on_message(self,vpin,msg):
#  print("on message",vpin,msg)
  for x in range(len(Settings.Tasks)):
   if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool:
    try:
     for u in range(Settings.Tasks[x].valuecount):
       vname = Settings.Tasks[x].valuenames[u]
       if vname != "":
        avname = vname.strip().lower().split(".")
        vvpin = -1
        if len(avname)>1:
         try:
          if avname[0][0] == "v":
           vvpin = int(avname[0][1:])
          else:
           vvpin = int(avname[0])
         except:
          vvpin = -1
         if int(vvpin) == int(vpin):
#          print("match",vname) # debug
          try:
           gval = msg[0]
          except:
           gval = str(msg)
          self.onmsgcallbackfunc(self.controllerindex,-1,gval,taskname=Settings.Tasks[x].gettaskname(),valuename=vname)
          return True
    except:
     pass
  return False

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled and BLYNK.blynkconnected:
    if tasknum!=-1:
     if changedvalue==-1:
      for u in range(Settings.Tasks[tasknum].valuecount):
       vname = Settings.Tasks[tasknum].valuenames[u]
       vpin = -1
       if vname != "":
        avname = vname.strip().lower().split(".")
        if len(avname)>1:
         try:
          if avname[0][0] == "v":
           vpin = int(avname[0][1:])
          else:
           vpin = int(avname[0])
         except:
          vpin = -1
       if (vpin<0) or (vpin>255):
        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Invalid Blynk VPIN: "+str(vpin)+" ("+str(vname)+")")
        return False
       try:
        BLYNK.blynk.virtual_write(vpin,str(value[u]))
       except Exception as e:
        print(e)
#       print("sending vpin ",vpin,":",str(value[u]))
     else:
       vname = Settings.Tasks[tasknum].valuenames[changedvalue-1]
       vpin = -1
       if vname != "":
        avname = vname.strip().lower().split(".")
        if len(avname)>1:
         try:
          if avname[0][0] == "v":
           vpin = int(avname[0][1:])
          else:
           vpin = int(avname[0])
         except:
          vpin = -1
       if (vpin<0) or (vpin>255):
        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Invalid Blynk VPIN: "+str(vpin)+" ("+str(vname)+")")
        return False
       try:
        BLYNK.blynk.virtual_write(vpin,str(value[u]))
       except Exception as e:
        print(e)
#       print("sending vpin ",vpin,":",str(value[u]))
