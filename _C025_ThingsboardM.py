#!/usr/bin/env python3
#############################################################################
############### Thingsboard MQTT controller for RPIEasy #####################
#############################################################################
#
# MQTT controller sends sensor data to:
#  sensor topic:   v1/devices/me/telemetry payload JSON name-value
#  actuator topic: v1/devices/me/attributes payload JSON name-value
#  subscribe: v1/devices/me/rpc/request/+
#
# Please make sure to use distinct names at task and valuenames!
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
import json

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 25
 CONTROLLER_NAME = "Thingsboard MQTT"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = True
  self.usesPassword = True
  self.usesMQTT = True
  self.onmsgcallbacksupported = True
  self.controllerport = 1883
  self.controllerip = "demo.thingsboard.io"
  self.inchannel = "v1/devices/me/attributes"
  self.outchannel = "v1/devices/me/rpc/request/+"
  self.telechannel = "v1/devices/me/telemetry"
  self.mqttclient = None
  self.lastreconnect = 0
  self.connectinprogress = 0
  self.inch = ""
  self.outch = ""
  self.authmode = 0
  self.certfile = ""
  self.laststatus = -1
  self.keepalive = 60
  self.useJSON = True
  self.backreport = True
  self.globalretain = False

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.connectinprogress = 0
  self.inch = str(self.inchannel)
  self.outch = str(self.outchannel)
  try:
   mqttcompatibility = mqtt.CallbackAPIVersion.VERSION1
  except:
   mqttcompatibility = None
  self.mqttclient = GMQTTClient(mqttcompatibility)
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
    if self.controllerpassword=="":
     self.mqttclient.username_pw_set(self.controlleruser)
    else:
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
    kp = self.keepalive
   except:
    self.keepalive = 60
   try:
    self.mqttclient.connect(self.controllerip,int(self.controllerport),keepalive=self.keepalive) # connect_async() is faster but maybe not the best for user/pass method
    self.mqttclient.loop_start()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MQTT controller: "+self.controllerip+":"+str(self.controllerport)+" connection failed "+str(e))
    self.laststatus = 0
  return self.isconnected()

 def disconnect(self):
   try:
         (mres,mid) = self.mqttclient.publish(self.telechannel,'{"online":false}')
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
    commands.rulesProcessing("ThingsMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)
   return stat

 def isconnected(self,ForceCheck=True):
  res = False
  if self.enabled and self.initialized:
   if ForceCheck==False:
    return (self.laststatus==1)
   if self.mqttclient is not None:
    mres = 1
    try:
     (mres,mid) = self.mqttclient.publish(self.telechannel,'{"online":true}')
    except Exception as e:
      mres = 1
    if mres==0:
     res = 1 # connected
    else:
     res = 0 # not connected
   if res != self.laststatus:
    if res==0:
     commands.rulesProcessing("ThingsMQTT#Disconnected",rpieGlobals.RULE_SYSTEM)
    else:
     commands.rulesProcessing("ThingsMQTT#Connected",rpieGlobals.RULE_SYSTEM)
    self.laststatus = res
   if res == 1 and self.connectinprogress==1:
    self.connectinprogress=0
  return res

 def webform_load(self): # create html page for settings
  webserver.addFormNote('Generate username on Thingsboard for the device!')
  webserver.addFormNote('Sensor data will appear as Telemetry, and Actuators will appear as Attribute. If you add a control widget, set "Subscribe for attribute" to get data and set "RPC set value method" to the same as the attribute name')
  try:
   kp = self.keepalive
  except:
   kp = 60
  webserver.addFormNumericBox("Keepalive time","keepalive",kp,2,600)
  webserver.addUnit("s")
  try:
   am = self.authmode
   fname = self.certfile
  except:
   am = 0
   fname = ""
  options = ["MQTT","MQTTS/with cert","MQTTS/insecure"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Mode","c025_mode",len(optionvalues),options,optionvalues,None,int(am))
  webserver.addFormTextBox("Server certificate file","c025_cert",str(fname),120)
  webserver.addBrowseButton("Browse","c025_cert",startdir=str(fname))
  webserver.addFormNote("Upload certificate first at <a href='filelist'>filelist</a> then select here!")
  webserver.addFormCheckBox("Check conn & reconnect if needed at every 30 sec","c025_reconnect",self.timer30s)
  return True

 def webform_save(self,params): # process settings post reply
  pchange = False
  try:
   p1 = self.authmode
   p2 = self.certfile
   self.authmode = int(webserver.arg("c014_mode",params))
   self.certfile = webserver.arg("c014_cert",params)
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
  if (webserver.arg("c025_reconnect",params)=="on"):
   self.timer30s = True
  else:
   self.timer30s = False

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
  tstart = self.outch.replace("+","")
  if msg.topic.startswith(tstart):
   msg2 = msg.payload.decode('utf-8')
   if self.useJSON:
      mlist = []
      if ('{' in msg2):
         try:
          mlist = json.loads(msg2)
         except Exception as e:
          mlist = []
      #print("msg",mlist) #debug
      if len(mlist)>0:
       if 'method' in mlist: #rpc call arrived
          reqname = mlist['method']
          if reqname == 'getGpioStatus':
           pval = mlist['params']
           if str(pval) == '{}':
             reply = {}
             try:
              for x in range(len(Settings.Tasks)):
               if Settings.Tasks[x] and type(Settings.Tasks[x]) is not bool and Settings.Tasks[x].enabled:
                if Settings.Tasks[x].recdataoption and Settings.Tasks[x].vtype == rpieGlobals.SENSOR_TYPE_SWITCH:
                 reply[str(x+1)] = (float(Settings.Tasks[x].uservar[0])==1)
             except Exception as e:
              print(e)
             reptopic = msg.topic.replace('request','response')
             replystr = json.dumps(reply)
             try:
                 (mres,mid) = self.mqttclient.publish(reptopic,replystr)
             except:
                 pass
           return True
          elif reqname == 'setGpioStatus':
           pval = mlist['params']
           if 'pin' in pval:
               val = False
               try:
                x = int(pval['pin'])-1
                if Settings.Tasks[x] and type(Settings.Tasks[x]) is not bool and Settings.Tasks[x].enabled:
                 if Settings.Tasks[x].recdataoption and Settings.Tasks[x].vtype == rpieGlobals.SENSOR_TYPE_SWITCH:
                    val = pval['enabled']
                    Settings.Tasks[x].set_value(1,val,True)
               except:
                val = False
               reply = {}
               reply[str(x+1)] = val
               reptopic = msg.topic.replace('request','response')
               replystr = json.dumps(reply)
               try:
                 (mres,mid) = self.mqttclient.publish(reptopic,replystr)
               except:
                 pass
           return True
          if '-' in reqname:
             ta = reqname.split("-")
             ttaskname = ta[0]
             valuename = ta[1]
          else:
             ttaskname = reqname
             valuename = ""
          pvalues = [-1,-1,-1,-1]
          if 'params' in mlist:
           pval = mlist['params']
           if pval is not None and str(pval) != 'None': ## setvalue arrived
             if str(pval).replace(".","").isnumeric():
              pvalues[0] = float(pval)
             elif pval == False or str(pval).lower() == 'false':
              pvalues[0] = 0
             elif pval == True or str(pval).lower() == 'true':
              pvalues[0] = 1
             else:
              pvalues[0] = str(pval)
             self.onmsgcallbackfunc(self.controllerindex,-1,pvalues,taskname=ttaskname,valuename="") #-> Settings.callback_from_controllers()
           else: ## getvalue arrived
             fv = -1
             try:
              for x in range(len(Settings.Tasks)):
               if Settings.Tasks[x] and type(Settings.Tasks[x]) is not bool:
                if Settings.Tasks[x].gettaskname().lower() == ttaskname.lower():
                 fv = x
                 break
             except:
              pass
             if fv > -1:
                val = Settings.Tasks[fv].uservar[0]
                reptopic = msg.topic.replace('request','response')
                reply = str(val)
                try:
                 (mres,mid) = self.mqttclient.publish(reptopic,reply)
                except:
                 pass
             else:
               print("Taskname not found:",ttaskname)
          else:
            print("No value arrived",mlist)
       return True
  return False

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled:
   if tasknum is None:
    return False
   if self.isconnected(False) and self.useJSON:
    if tasknum!=-1:
       tname = Settings.Tasks[tasknum].gettaskname()
       gval = '{'
       for u in range(Settings.Tasks[tasknum].valuecount):
           gval += '"'+ tname + "-"+ Settings.Tasks[tasknum].valuenames[u] + '":'
           val = value[u]
           if str(val).replace(".","").isnumeric():
            gval += str(val)
           else:
            gval += '"'+ str(val) +'"'
           gval += ","
       if Settings.Tasks[tasknum].recdataoption:
        gtopic = self.inch         #control dev, send as attribute
       else:
        gtopic = self.telechannel  #sensor send as telemetry
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
           gval += '"' + tname + '-battery":'+ str(bval)+ ','
        if userssi != -1:
           gval += '"' + tname + '-rssi":'+ str(userssi)+ ','
       gval = gval[:-1]+"}"
       mres = 1
       try:
         (mres,mid) = self.mqttclient.publish(gtopic,gval,retain=self.globalretain)
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
