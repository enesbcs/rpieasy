#!/usr/bin/env python3
#############################################################################
############### Autodiscovery MQTT controller for RPIEasy ###################
#############################################################################
#
# HA/Domoticz Autodiscovery MQTT controller sends sensor data to:
#  topic: %sysname%/taskname/valuename with payload: value
#
# Please make sure to use distinct names at task and valuenames!
#
# If the target device implements plugin_receivedata() than the
#  topic: %sysname%/taskname/valuename/set payload value will be forwarded to it!
# (Two way communication)
#
# Variables: %sysname% %tskname% %valname% %tskid%
#  # = %tskname%/%valname% !!!
#
# Commands can be remotely executed through MQTT with writing to:
#  topic: %sysname%/cmd with payload: command
#
# Copyright (C) 2018-2023 by Alexander Nagy - https://bitekmindenhol.blog.hu/
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
import lib.lib_mqttad as mqttad
import json

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 24
 CONTROLLER_NAME = "Autodiscovery MQTT [TESTING]"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = True
  self.usesPassword = True
  self.usesMQTT = True
  self.onmsgcallbacksupported = True
  self.controllerport = 1883
  self.inchannel = "%sysname%/#"
  self.outchannel = "%sysname%/#/set"
  self.mqttclient = None
  self.lastreconnect = 0
  self.connectinprogress = 0
  self.inch = ""
  self.outch = ""
  self.authmode = 0
  self.certfile = ""
  self.laststatus = -1
  self.keepalive = 60
  self.lwt_topic = "%sysname%/online"
  self.lwt_t = ""
  self.lwtconnmsg = "true"
  self.lwtdisconnmsg = "false"
  self.backreport = True
  self.globalretain = False
  self.retainconfig = True
  self.discoverytopic = "homeassistant"
  self.adconffile = "data/adconf.json"

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.connectinprogress = 0
  self.inch, state = commands.parseruleline(self.inchannel)    # replace global variables
  self.outch, state = commands.parseruleline(self.outchannel)
  state = self.outch.find('#')
  if state >-1:
   self.outch = self.outch[:(state+1)]
  else:
   state = self.outch.find('%tskname%')
   if state < 0:
    state = self.outch.find('%tskid%')
   if state >-1:
    self.outch = self.outch[:(state)]+"/#"
   else:
    state = self.outch.find('%valname%')
    if state >-1:
     self.outch = self.outch[:(state)]+"/#"
  self.outch = self.outch.replace('//','/').strip()
  if self.outch=="" or self.outch=="/" or self.outch=="/#" or self.outch=="%/#":
   self.outch = "#"
  try:
   ls = self.laststatus
  except:
   self.laststatus = -1

  try:
   self.lwt_t, state = commands.parseruleline(self.lwt_topic)
  except:
   self.lwt_topic = ""
  self.mqttclient = GMQTTClient()
  self.mqttclient.subscribechannel = self.outch
  self.mqttclient.controllercb = self.on_message
  self.mqttclient.connectcb = self.on_connect
  self.mqttclient.disconnectcb = self.on_disconnect
  if self.controllerpassword=="*****":
   self.controllerpassword=""
  self.initialized = True
  if self.enabled:
   if self.isconnected()==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MQTT: Try to connect")
    self.connect()
   self.sendconfig()
  else:
   self.laststatus = -1
   self.disconnect()
  return True

 def connect(self):
  if self.enabled and self.initialized:
   if self.isconnected():
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Already connected force disconnect!")
    self.disconnect()
   self.connectinprogress = 1
   self.lastreconnect = time.time()
   if (self.controlleruser!="" or self.controllerpassword!="") and (self.isconnected() == False):
    self.mqttclient.username_pw_set(self.controlleruser,self.controllerpassword)
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Set MQTT password")
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
    self.mqttclient.will_set(self.lwt_t, payload=self.lwtdisconnmsg, qos=0, retain=True)
    self.mqttclient.connect(self.controllerip,int(self.controllerport),keepalive=self.keepalive) # connect_async() is faster but maybe not the best for user/pass method
    self.mqttclient.loop_start()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT controller: "+self.controllerip+":"+str(self.controllerport)+" connection failed "+str(e))
    self.laststatus = 0
  return self.isconnected()

 def disconnect(self):
   try:
         (mres,mid) = self.mqttclient.publish(self.lwt_t,self.lwtdisconnmsg)
   except Exception as e:
         print(e)
   try:
    self.mqttclient.loop_stop(True)
   except:
    pass
   try:
    self.mqttclient.disconnect()
   except:
    pass
   stat=self.isconnected()
   if self.enabled!=True:
    commands.rulesProcessing("ADMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)
   return stat

 def isconnected(self,ForceCheck=True):
  res = False
  if self.enabled and self.initialized:
   if ForceCheck==False:
    return (self.laststatus==1)
   if self.mqttclient is not None:
    tstart = self.outch[:len(self.outch)-1]
    gtopic = tstart+"status"
    gval   = "PING"
    mres = 1
    try:
     (mres,mid) = self.mqttclient.publish(gtopic,gval)
    except:
      mres = 1
    if mres==0:
     res = 1 # connected
    else:
     res = 0 # not connected
   if res != self.laststatus:
    if res==0:
     commands.rulesProcessing("ADMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)
    else:
     try:
         (mres,mid) = self.mqttclient.publish(self.lwt_t,self.lwtconnmsg,retain=True)
     except:
         pass
     commands.rulesProcessing("ADMQTT#Connected",rpieGlobals.RULE_SYSTEM)
    self.laststatus = res
   if res == 1 and self.connectinprogress==1:
    self.connectinprogress=0
  return res

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Discovery topic","dtopic",self.discoverytopic,255)
  webserver.addHtml("</td></tr><tr><td></td><td><a href='/adconfig?cid="+ str(self.controllerindex) +"'>Open device configuration page</a></td></tr>")
  webserver.addFormNumericBox("Keepalive time","keepalive",self.keepalive,2,600)
  webserver.addUnit("s")
  try:
   am = self.authmode
   fname = self.certfile
  except:
   am = 0
   fname = ""
  options = ["MQTT","MQTTS/with cert","MQTTS/insecure"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Mode","c024_mode",len(optionvalues),options,optionvalues,None,int(am))
  webserver.addFormTextBox("Server certificate file","c024_cert",str(fname),120)
  webserver.addBrowseButton("Browse","c024_cert",startdir=str(fname))
  webserver.addFormNote("Upload certificate first at <a href='filelist'>filelist</a> then select here!")
  webserver.addFormCheckBox("Check conn & reconnect if needed at every 30 sec","c024_reconnect",self.timer30s)
  webserver.addFormCheckBox("Retain config AD messages","c024_confretain",self.retainconfig)
  webserver.addFormNote("Enable retain config AFTER you have created all devices, config is final and you wants it to survive reboot!")
  webserver.addFormCheckBox("Retain every message","c024_retain",self.globalretain)
  return True

 def webform_save(self,params): # process settings post reply
  pchange = False
  pval = self.discoverytopic
  self.discoverytopic = webserver.arg("dtopic",params)
  if pval != self.discoverytopic:
   pchange = True
  if self.inchannel == self.outchannel:
   self.outchannel = self.outchannel+"/set"
  try:
   p1 = self.authmode
   p2 = self.certfile
   self.authmode = int(webserver.arg("c024_mode",params))
   self.certfile = webserver.arg("c024_cert",params)
   if p1 != self.authmode or p2 != self.certfile:
    pchange = True
  except:
   self.authmode = 0
   self.certfile = ""
  pval = self.keepalive
  try:
   self.keepalive = int(webserver.arg("keepalive",params))
  except:
   self.keepalive = 60
  if pval != self.keepalive:
   pchange = True
  if (webserver.arg("c024_reconnect",params)=="on"):
   self.timer30s = True
  else:
   self.timer30s = False
  if (webserver.arg("c024_retain",params)=="on"):
   self.globalretain = True
  else:
   self.globalretain = False
  if (webserver.arg("c024_confretain",params)=="on"):
   self.retainconfig = True
  else:
   self.retainconfig = False

  if pchange and self.enabled:
   self.disconnect()
   time.sleep(0.1)
   self.connect()
  return True

 def timer_thirty_second(self):
  if self.enabled:
   if self.isconnected()==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MQTT: Try to reconnect")
    self.connect()
  return self.timer30s

 def on_message(self, msg):
  success = False
  tstart = self.outch[:len(self.outch)-1]
  if msg.topic.startswith(tstart) or self.outch=="#":
   msg2 = msg.payload.decode('utf-8')
   if (msg.topic == tstart + "cmd") and (self.outch!="#"):   # global command arrived, execute
    commands.doExecuteCommand(msg2,True)
    success = True
   else:
    try:
#      tend = msg.topic[len(self.outch)-1:]
      dnames = msg.topic.split("/")
      dnames2 = self.outchannel.split("/")
    except:
      dnames = []
    if len(dnames)>1:
     v1 = -1
     v2 = -1
     if self.outchannel.endswith("/"+dnames[len(dnames)-1]): # set command arrived, forward it to the Task
      ttaskname = ""
      if ('{' in msg2): #possible json payload
       try:
        mlist = json.loads(msg2)
       except:
        mlist = []
       if ('brightness' in mlist): #check for incoming dimmer set
          msg2 = mlist['brightness'] #overwrite whole payload with brightness value (Domoticz!)
      #print(msg2,mlist,ttaskname,dnames)#debug
      if ttaskname=="":
       try:
        v1 = dnames2.index("#")
        v2 = v1+1
       except:
        v1 = -1
       if v1 == -1:
        try:
         v1 = dnames2.index("%tskname%")
        except:
         v1 = -1
        try:
         v2 = dnames2.index("%valname%")
        except:
         v2 = -1
        try:
         v3 = dnames2.index("%tskid%")
        except:
         v3 = -1
        if v3>-1:
         try:
           t = int(dnames[v3])-1
           if Settings.Tasks[t] and type(Settings.Tasks[t]) is not bool:
             ttaskname = Settings.Tasks[t].gettaskname().strip()
         except:
          pass
        elif v1==-1 and v2>-1:
         try:
          for x in range(len(Settings.Tasks)):
           if Settings.Tasks[x] and type(Settings.Tasks[x]) is not bool:
            for u in range(Settings.Tasks[x].valuecount):
             if Settings.Tasks[x].valuenames[u] == dnames[v2]:
              ttaskname = Settings.Tasks[x].gettaskname().strip()
              break
            if ttaskname != "":
             break
         except:
          pass
       if ttaskname=="" and v1>-1:
         ttaskname = dnames[v1]

      if ttaskname != "" and v2>-1 and v2<len(dnames):
       self.onmsgcallbackfunc(self.controllerindex,-1,msg2,taskname=ttaskname,valuename=dnames[v2]) #-> Settings.callback_from_controllers()
       success = True

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled:
   if tasknum is None:
    return False
   success = False
   if self.isconnected(False):
    if tasknum!=-1:
     tname = Settings.Tasks[tasknum].gettaskname()
     if changedvalue==-1:
      for u in range(Settings.Tasks[tasknum].valuecount):
       vname = Settings.Tasks[tasknum].valuenames[u]
       if vname != "":
        if ('%t' in self.inch) or ('%v' in self.inch):
         gtopic = self.inch.replace('#/','')
         gtopic = gtopic.replace('#','')
         gtopic = gtopic.replace('%tskname%',tname)
         gtopic = gtopic.replace('%tskid%',str(tasknum+1))
         gtopic = gtopic.replace('%valname%',vname)
        else:
         gtopic = self.inch.replace('#',tname+"/"+vname)
        gval = str(value[u])
        if gval == "":
         gval = "0"
        mres = 1
        try:
         (mres,mid) = self.mqttclient.publish(gtopic,gval,retain=self.globalretain)
#         print(gtopic) # DEBUG
        except:
         mres = 1
        if mres!=0:
         self.isconnected()
         break
     else:
      vname = Settings.Tasks[tasknum].valuenames[changedvalue-1]
      if ('%t' in self.inch) or ('%v' in self.inch):
         gtopic = self.inch.replace('#/','')
         gtopic = gtopic.replace('#','')
         gtopic = gtopic.replace('%tskname%',tname)
         gtopic = gtopic.replace('%tskid%',str(tasknum+1))
         gtopic = gtopic.replace('%valname%',vname)
      else:
         gtopic = self.inch.replace('#',tname+"/"+vname)
      if vname != "":
       gval = str(value[changedvalue-1])
       if gval == "":
         gval = "0"
       mres = 1
       try:
         (mres,mid) = self.mqttclient.publish(gtopic,gval,retain=self.globalretain)
#         print(gtopic,gval) # DEBUG
       except:
         mres = 1
       if mres!=0:
         self.isconnected()
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT taskname error, sending failed.")
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT not connected, sending failed.")
    if (time.time()-self.lastreconnect)>30:
     self.connect()

 def on_connect(self):
  if self.enabled and self.initialized:
   self.isconnected()
  else:
   self.disconnect()

 def on_disconnect(self):
  if self.initialized:
   self.isconnected()

 def sendconfig(self):
     t = mqttad.ADHelper(self.discoverytopic,Settings.Settings["Name"],self.controllerindex)
     confs = t.get_MQTT_strs()
     confs = t.add_static_mstrs(self.adconffile,confs)
     if len(confs)>0:
      mres = 0
      for cd in range(len(confs)):
          for cl in range(len(confs[cd]['config'])):
             try:
              (mres,mid) = self.mqttclient.publish(confs[cd]['config'][cl][0],confs[cd]['config'][cl][1],retain=self.retainconfig)
             except:
              mres = 1
     #print("config",confs)#debug

class GMQTTClient(mqtt.Client):
 subscribechannel = ""
 controllercb = None
 disconnectcb = None
 connectcb = None

 def on_connect(self, client, userdata, flags, rc):
  try:
   self.subscribe(self.subscribechannel,0)
   if self.connectcb is not None:
    self.connectcb()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT connection error: "+str(e))
  try:
   rc = int(rc)
  except:
   rc=-1
  if rc !=0:
   estr = str(rc)
   if rc==1:
      estr += " Protocol version error!"
   if rc==3:
      estr += " Server unavailable!"
   if rc==4:
      estr += " User/pass error!"
   if rc==5:
      estr += " Not authorized!"
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT connection error: "+estr)

 def on_disconnect(self, client, userdata, rc):
  if self.disconnectcb is not None:
    self.disconnectcb()

 def on_message(self, mqttc, obj, msg):
  if self.controllercb is not None:
   self.controllercb(msg)
 