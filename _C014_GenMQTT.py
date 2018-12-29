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
  self.inch = ""
  self.outch = ""

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.initialized = True
  self.inch, state = commands.parseruleline(self.inchannel)    # replace global variables
  self.outch, state = commands.parseruleline(self.outchannel)
  state = self.outch.find('#')
  if state >-1:
   self.outch = self.outch[:(state+1)]
  if self.enabled:
   self.mqttclient = GMQTTClient()
   self.mqttclient.subscribechannel = self.outch
   self.mqttclient.controllercb = self.on_message
   self.connect()
  else:
   self.disconnect()
  return True

 def connect(self):
  if self.enabled and self.initialized:
   if self.mqttclient.connected:
    self.disconnect()
   self.lastreconnect = time.time()
   if self.controlleruser!="" or self.controllerpassword!="":
    self.mqttclient.username_pw_set(username=self.controlleruser,password=self.controllerpassword)
   try:
    self.mqttclient.connect_async(self.controllerip,int(self.controllerport))
    self.mqttclient.loop_start()
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT controller: "+self.controllerip+" connection failed")
  return self.mqttclient.connected

 def disconnect(self):
  try:
   self.mqttclient.loop_stop(True)
   self.mqttclient.disconnect()
  except:
   pass
  return self.mqttclient.connected

 def isconnected(self):
  res = False
  if self.enabled and self.initialized:
   if self.mqttclient:
    try:
     res = self.mqttclient.connected
    except:
     res = False
  return res

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Report topic","inchannel",self.inchannel,255)
  webserver.addFormTextBox("Command topic","outchannel",self.outchannel,255)
  return True

 def webform_save(self,params): # process settings post reply
  self.inchannel = webserver.arg("inchannel",params)
  self.outchannel = webserver.arg("outchannel",params)
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

class GMQTTClient(mqtt.Client):
 subscribechannel = ""
 controllercb = None
 connected = False

 def on_connect(self, client, userdata, flags, rc):
  if rc==0:
   self.subscribe(self.subscribechannel,0)
   self.connected = True
   commands.rulesProcessing("GenMQTT#Connected",rpieGlobals.RULE_SYSTEM)

 def on_disconnect(self, client, userdata, rc):
  self.connected = False
  commands.rulesProcessing("GenMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)

 def on_message(self, mqttc, obj, msg):
  if self.connected and self.controllercb:
   self.controllercb(msg)
