#!/usr/bin/env python3
#############################################################################
################ Generic MQTT controller for RPIEasy ########################
#############################################################################
#
# Generic MQTT controller sends sensor data to:
#  topic: %sysname%/taskname/valuename/state with payload: value
#
# Please make sure to use distinct names at task and valuenames!
#
# If the target device implements plugin_receivedata() than the
#  topic: %sysname%/taskname/valuename/set payload value will be forwarded to it!
# (Two way communication)
#
# Commands can be remotely executed through MQTT with writing to:
#  topic: %sysname%/cmd with payload: command
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import paho.mqtt.client as mqtt
import misc
import rpieGlobals
import time
import webserver
import commands
import Settings
import os

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 14
 CONTROLLER_NAME = "Generic MQTT"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = True
  self.usesPassword = True
  self.usesMQTT = True
  self.onmsgcallbacksupported = True
  self.controllerport = 1883
  self.inchannel = "%sysname%/#/state"
  self.outchannel = "%sysname%/#/set" # webformload?
  self.mqttclient = None
  self.lastreconnect = 0
  self.connectinprogress = 0
  self.inch = ""
  self.outch = ""
  self.authmode = 0
  self.certfile = ""
  self.laststatus = -1

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.connectinprogress = 0
  self.inch, state = commands.parseruleline(self.inchannel)    # replace global variables
  self.outch, state = commands.parseruleline(self.outchannel)
  state = self.outch.find('#')
  if state >-1:
   self.outch = self.outch[:(state+1)]
  self.mqttclient = GMQTTClient()
  self.mqttclient.subscribechannel = self.outch
  self.mqttclient.controllercb = self.on_message
  self.mqttclient.connectcb = self.on_connect
  self.mqttclient.disconnectcb = self.on_disconnect
  self.initialized = True
  if self.enabled:
   self.connect()
  else:
   self.disconnect()
  return True

 def connect(self):
  if self.enabled and self.initialized:
   if self.isconnected():
    self.disconnect()
   self.connectinprogress = 1
   self.lastreconnect = time.time()
   if self.controlleruser!="" or self.controllerpassword!="":
    self.mqttclient.username_pw_set(username=self.controlleruser,password=self.controllerpassword)
   try:
    am = self.authmode
   except:
    am = 0
   if am==1 or am==2: # mqtts
     try:
      import ssl
     except:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OpenSSL is not reachable!")
      self.initialized = False
      return False
     if am==1: # with cert file
      try:
       fname = self.certfile.strip()
      except:
       fname = ""
      if (fname=="") or (str(fname)=="0") or (os.path.exists(fname)==False):
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Certificate file not found!")
       self.initialized = False
       return False
      try:
       self.mqttclient.tls_set(fname, tls_version=ssl.PROTOCOL_TLSv1_2)
       self.mqttclient.tls_insecure_set(True) # or False?
      except:
       pass
     elif am==2: # no cert! connect somehow..
      try:
       ssl_ctx = ssl.create_default_context()
       ssl_ctx.check_hostname = False
       ssl_ctx.verify_mode = ssl.CERT_NONE
       self.mqttclient.tls_set_context(ssl_ctx)
       self.mqttclient.tls_insecure_set(True)
      except:
       pass
   try:
    self.mqttclient.connect_async(self.controllerip,int(self.controllerport))
    self.mqttclient.loop_start()
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT controller: "+self.controllerip+":"+str(self.controllerport)+" connection failed")
  return self.isconnected()

 def disconnect(self):
   try:
    self.mqttclient.loop_stop(True)
    self.mqttclient.disconnect()
    self.mqttclient.connected=False
   except:
    pass
   stat=self.isconnected()
   if stat==False:
    self.on_disconnect()
   return stat

 def isconnected(self):
  res = False
  if self.enabled and self.initialized:
   if self.mqttclient is not None:
    try:
     res = self.mqttclient.connected
    except:
     res = False
  return res

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Report topic","inchannel",self.inchannel,255)
  webserver.addFormTextBox("Command topic","outchannel",self.outchannel,255)
  try:
   am = self.authmode
   fname = self.certfile
  except:
   am = 0
   fname = ""
  options = ["MQTT","MQTTS/with cert","MQTTS/insecure"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Mode","c014_mode",len(optionvalues),options,optionvalues,None,int(am))
  webserver.addFormTextBox("Server certificate file","c014_cert",str(fname),120)
  webserver.addBrowseButton("Browse","c014_cert",startdir=str(fname))
  webserver.addFormNote("Upload certificate first at <a href='filelist'>filelist</a> then select here!")
  return True

 def webform_save(self,params): # process settings post reply
  self.inchannel = webserver.arg("inchannel",params)
  self.outchannel = webserver.arg("outchannel",params)
  try:
   self.authmode = int(webserver.arg("c014_mode",params))
   self.certfile = webserver.arg("c014_cert",params)
  except:
   self.authmode = 0
   self.certfile = ""
  return True

 def on_message(self, msg):
  success = False
  tstart = self.outch[:len(self.outch)-1]
  if msg.topic.startswith(tstart):
   msg2 = msg.payload.decode('utf-8')
   if msg.topic == tstart + "cmd":   # global command arrived, execute
    commands.doExecuteCommand(msg2,True) 
    success = True
   else:
    try:
     tend = msg.topic[len(self.outch)-1:]
     dnames = tend.split("/")
    except:
     dnames = []
    if len(dnames)>2:
     if self.outchannel.endswith("/"+dnames[len(dnames)-1]): # set command arrived, forward it to the Task
      self.onmsgcallbackfunc(self.controllerindex,-1,msg2,taskname=dnames[0],valuename=dnames[1]) #-> Settings.callback_from_controllers()
      success = True

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled:
   success = False
   if self.isconnected():
    if tasknum!=-1:
     tname = Settings.Tasks[tasknum].gettaskname()
     if changedvalue==-1:
      for u in range(Settings.Tasks[tasknum].valuecount):
       vname = Settings.Tasks[tasknum].valuenames[u]
       if vname != "":
        gtopic = self.inch.replace('#',tname+"/"+vname)
        gval = str(value[u])
        if gval == "":
         gval = "0"
        self.mqttclient.publish(gtopic,gval)
     else:
      vname = Settings.Tasks[tasknum].valuenames[changedvalue-1]
      gtopic = self.inch.replace('#',tname+"/"+vname)
      if vname != "":
       gval = str(value[changedvalue-1])
       if gval == "":
         gval = "0"
       self.mqttclient.publish(gtopic,gval)
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT taskname error, sending failed.")
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT not connected, sending failed.")
    if (time.time()-self.lastreconnect)>30:
     self.connect()

 def on_connect(self):
  if self.enabled and self.initialized:
   if self.connectinprogress==1:
    commands.rulesProcessing("GenMQTT#Connected",rpieGlobals.RULE_SYSTEM)
    self.laststatus = 1
    self.connectinprogress=0
  else:
   self.disconnect()

 def on_disconnect(self):
  if self.initialized:
   if self.laststatus==1:
    commands.rulesProcessing("GenMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)
    self.laststatus = 0

class GMQTTClient(mqtt.Client):
 subscribechannel = ""
 controllercb = None
 connected = False
 disconnectcb = None
 connectcb = None

 def on_connect(self, client, userdata, flags, rc):
  if rc==0:
   self.subscribe(self.subscribechannel,0)
   self.connected = True
   if self.connectcb is not None:
    self.connectcb()

 def on_disconnect(self, client, userdata, rc):
  self.connected = False
  if self.disconnectcb is not None:
    self.disconnectcb()

 def on_message(self, mqttc, obj, msg):
  if self.connected and self.controllercb is not None:
   self.controllercb(msg)
 