#!/usr/bin/env python3
#############################################################################
################## Domoticz MQTT controller for RPIEasy #####################
#############################################################################
#
# Two way MQTT communication with Domoticz server. (Plugins that implements
# plugin_receivedata() function will receive commands if they register the
# appropriate IDX)
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# missing! complete it based on c014!
import controller
import paho.mqtt.client as mqtt
import json
import misc
import rpieGlobals
import time
import re
import webserver
import commands
from helper_domoticz import *
import os

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 2
 CONTROLLER_NAME = "Domoticz MQTT"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = True
  self.onmsgcallbacksupported = True
  self.controllerport = 1883
  self.inchannel = "domoticz/in"
  self.outchannel = "domoticz/out" # webformload?
  self.mqttclient = None
  self.lastreconnect = 0
  self.usesAccount = True
  self.usesPassword = True
  self.usesMQTT = True
  self.authmode = 0
  self.certfile = ""
  self.laststatus = False

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.connectinprogress = 0
  self.laststatus = False
  self.mqttclient = DMQTTClient()
  self.mqttclient.subscribechannel = self.outchannel
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
  return self.mqttclient.connected

 def disconnect(self):
  try:
   self.mqttclient.loop_stop(True)
   self.mqttclient.disconnect()
   self.mqttclient.connected=False
  except:
   pass
  return self.isconnected()

 def isconnected(self):
  res = False
  if self.enabled and self.initialized:
   if self.mqttclient is not None:
    try:
     res = self.mqttclient.connected
    except:
     res = False
  self.laststatus = res
  return res

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Controller Publish","inchannel",self.inchannel,255)
  webserver.addFormTextBox("Controller Subscribe","outchannel",self.outchannel,255)
  try:
   am = self.authmode
   fname = self.certfile
  except:
   am = 0
   fname = ""
  options = ["MQTT","MQTTS/with cert","MQTTS/insecure"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Mode","c002_mode",len(optionvalues),options,optionvalues,None,int(am))
  webserver.addFormTextBox("Server certificate file","c002_cert",str(fname),120)
  webserver.addBrowseButton("Browse","c002_cert",startdir=str(fname))
  webserver.addFormNote("Upload certificate first at <a href='filelist'>filelist</a> then select here!")
  return True

 def webform_save(self,params): # process settings post reply
  self.inchannel = webserver.arg("inchannel",params)
  self.outchannel = webserver.arg("outchannel",params)
  try:
   self.authmode = int(webserver.arg("c002_mode",params))
   self.certfile = webserver.arg("c002_cert",params)
  except:
   self.authmode = 0
   self.certfile = ""
  return True

 def on_message(self, msg):
  msg2 = msg.payload.decode('utf-8')
  list = []
  if ('{' in msg2):
   try:
    list = json.loads(msg2)
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"JSON decode error:"+str(e)+str(msg2))
    list = []
  if (list) and (len(list)>0):
   try:
    if list['Type'] == "Scene": # not interested in scenes..
     return False
   except:
    pass
   devidx = -1
   nvalue = "0"
   svalue = ""
   decodeerr = False
   tval = [-1,-1,-1,-1]
   try:
    devidx = str(list['idx']).strip()
   except:
    devidx = -1
    decodeerr = True
   try:
    nvalue = str(list['nvalue']).strip()
   except:
    nvalue = "0"
    decodeerr = True
   try:
    svalue = str(list['svalue']).strip()
   except:
    svalue = ""
   if (';' in svalue):
    tval = svalue.split(';')
   tval2 = []
   for x in range(1,4):
    sval = ""
    try:
     sval = str(list['svalue'+str(x)]).strip()
    except:
     sval = ""
    if sval!="":
     tval2.append(sval)
   if len(tval2)==1 and svalue=="":
    svalue=tval2[0]
   else:
    for y in range(len(tval2)):
      matches = re.findall('[0-9]', tval2[y])
      if len(matches) > 0:
       tval[y] = tval2[y]
   forcesval1 = False
   try:
    if list['switchType'] == "Selector":
     forcesval1 = True
   except:
    forcesval1 = False
   if (tval[0] == -1) or (tval[0] == ""):
    if (float(nvalue)==0 and svalue.lower()!="off" and svalue!="") or (forcesval1):
     tval[0] = str(svalue)
    else:
     tval[0] = str(nvalue)
   if decodeerr:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"JSON decode error: "+msg2)
   else:
    self.onmsgcallbackfunc(self.controllerindex,devidx,tval)

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled:
   mStates = ["Off","On"]
#   domomsg = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}" }}'
   domomsgw = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "RSSI": {3} }}'
   domomsgwb = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "RSSI": {3}, "Battery": {4} }}'
   domosmsgw = '{{"command": "switchlight", "idx": {0}, "switchcmd": "Set Level", "level":"{1}", "RSSI": {2} }}'
   domosmsgwb = '{{"command": "switchlight", "idx": {0}, "switchcmd": "Set Level", "level":"{1}", "RSSI": {2}, "Battery": {3} }}'
   if self.isconnected():
    if int(idx) > 0:
     if usebattery != -1 and usebattery != 255:
      bval = usebattery
     else:
      bval = misc.get_battery_value()
     msg = ""
     if (int(sensortype)==rpieGlobals.SENSOR_TYPE_SWITCH):
      try:
       stateid = int(round(value[0]))
      except:
       stateid = 0
      if stateid<0:
       stateid = 0
      if stateid>1:
       stateid = 1
      msg = domomsgwb.format(str(idx), int(stateid), mStates[stateid], mapRSSItoDomoticz(userssi),str(bval))
     elif (int(sensortype)==rpieGlobals.SENSOR_TYPE_DIMMER):
      msg = domosmsgwb.format(str(idx), str(value[0]), mapRSSItoDomoticz(userssi),str(bval))
     else:
      msg = domomsgwb.format(str(idx), 0, formatDomoticzSensorType(sensortype,value), mapRSSItoDomoticz(userssi),str(bval))
#     print(msg) #DEBUG
     self.mqttclient.publish(self.inchannel,msg)
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT idx error, sending failed.")
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT not connected, sending failed.")
    if (time.time()-self.lastreconnect)>30:
     self.connect()

 def on_connect(self):
  if self.enabled and self.initialized:
   if self.connectinprogress==1:
    commands.rulesProcessing("DomoMQTT#Connected",rpieGlobals.RULE_SYSTEM)
    self.connectinprogress=0
  else:
   self.disconnect()

 def on_disconnect(self):
  if self.enabled and self.initialized:
   if self.laststatus:
    commands.rulesProcessing("DomoMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)

class DMQTTClient(mqtt.Client):
 subscribechannel = ""
 controllercb = None
 connected = False
 disconnectcb = None
 connected = False

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
  if self.connected and self.controllercb:
   self.controllercb(msg)
