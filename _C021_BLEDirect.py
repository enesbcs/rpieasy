#!/usr/bin/env python3
#############################################################################
################## BLE Direct controller for RPIEasy ########################
#############################################################################
#
# This controller is able to listen or send BLE messages to nearby devices
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import misc
import rpieGlobals
import time
from rpieTime import *
import webserver
import commands
import Settings
from datetime import datetime
import lib.lib_p2pbuffer as p2pbuffer
from pybleno import *
from bluepy.btle import Peripheral
import os
import linux_os as OS

BLE_SERVICE_ID    = "5032505f-5250-4945-6173-795f424c455f"
BLE_RECEIVER_CHAR = "10000001-5250-4945-6173-795f424c455f"
BLE_INFO_CHAR     = "10000002-5250-4945-6173-795f424c455f"

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 21
 CONTROLLER_NAME = "BLE Direct (EXPERIMENTAL)"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = True
  self.onmsgcallbacksupported = False # use direct set_value() instead of generic callback to make sure that values setted anyway
  self.controllerport = 1
  self.bleserv = None
  self.bleclient = None
  self.timer30s = True
  self.duty = 0  # use 100%
  self.defaultdestination = ""
  self.defaultunit = 1
  self.lastsysinfo = 0
  self.sysinfoperiod = 1800 # seconds
  self.enablerec = True
  self.enablesend = False
  self.directsend = False

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.initialized = False
  if self.enabled:
   if int(Settings.Settings["Unit"])>0:
    self.controllerport = Settings.Settings["Unit"]
   self.lastsysinfo = 0
   if self.bleserv is not None:
    try:
     self.bleserv.stop()
     time.sleep(1)
    except:
     pass
   try:
    output = os.popen(OS.cmdline_rootcorrect("sudo systemctl stop bluetooth"))
    for l in output:
     pass
   except Exception as e:
    print(e)
   try:
    output = os.popen(OS.cmdline_rootcorrect("sudo hciconfig hci0 up"))
    for l in output:
     pass
   except Exception as e:
    print(e)
   try:
    self.bleclient = BLEClient(self.defaultdestination,self.duty)
    self.bleserv = BLEServer(Settings.Settings["Name"],self.pkt_receiver,self.getmode)
    if self.enablerec:
     self.bleserv.start()
    if self.enablesend==False:
     self.defaultdestination=""
    self.initialized = True
    time.sleep(1)
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BLE Direct initialized")
   except Exception as e:
    self.initialized = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE Direct init error: "+str(e))
  else:
   if self.bleserv is not None:
    try:
     self.bleserv.stop()
    except:
     pass
  return True

 def controller_exit(self):
   if self.bleserv is not None:
    try:
     self.bleserv.stop()
    except:
     pass
 
 def webform_load(self):
  webserver.addFormNote("IP and Port parameter is not used!")
  webserver.addFormCheckBox("Enable Receiver Service","receiver",self.enablerec)
  webserver.addFormNote("Enable this for Gateway/Repeater unit, Disable if you only want to send data!")
  try:
   if self.bleserv is not None:
    webserver.addFormNote("Current Address: "+str(self.bleserv.getaddress()))
  except:
   pass
  webserver.addFormCheckBox("Enable Sending to Default Master Unit","sender",self.enablesend)
  webserver.addFormCheckBox("Enable Direct Sending to Units in P2P list","directsender",self.directsend)
  webserver.addFormNote("Please respect MASTER-SLAVE nature of BLE and do not create infinite loops!")
  webserver.addFormTextBox("Default BLE Master Unit address","masteraddress",self.defaultdestination,23)
  webserver.addFormNote("Enable bluetooth then <a href='blescanner'>scan RPIEasy BLE address</a> first.")
  webserver.addFormNumericBox("Default destination node index","defaultnode",self.defaultunit,0,255)
  webserver.addFormNote("Default node index for data sending, only used when Master Unit address is setted")
  return True

 def webform_save(self,params):
  try:
   self.enablerec = (webserver.arg("receiver",params)=="on")
   self.enablesend = (webserver.arg("sender",params)=="on")
   self.directsend = (webserver.arg("directsender",params)=="on")
   self.defaultdestination = str(webserver.arg("masteraddress",params)).strip()
   if len(self.defaultdestination)<13:
    self.defaultdestination = ""
   self.defaultunit = int(webserver.arg("defaultnode",params))
#   self.controller_init()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE parameter save: "+str(e))
  return True

 def nodesort(self,item):
  v = 0
  try:
   v = int(item["unitno"])
  except:
   v = 0
  return v

 def pkt_receiver(self,payload): # processing incoming packets
#  print(payload) # debug
  if self.enabled:
    dp = p2pbuffer.data_packet() 
    dp.buffer = payload
    dp.decode()            # asking p2pbuffer library to decode it
    if dp.pkgtype!=0:
        if dp.pkgtype==1: # info packet received
#         print(dp.infopacket)
         if int(dp.infopacket["unitno"]) == int(Settings.Settings["Unit"]): # skip own messages
          return False
         un = getunitordfromnum(dp.infopacket["unitno"]) # process incoming alive reports
         if un==-1:
          # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
          Settings.p2plist.append({"protocol":"BLE","unitno":dp.infopacket["unitno"],"name":dp.infopacket["name"],"build":dp.infopacket["build"],"type":dp.infopacket["type"],"mac":dp.infopacket["mac"],"lastseen":datetime.now(),"lastrssi":self.bleserv.getrssi(),"cap":dp.infopacket["cap"]})
          misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"New BLE unit discovered: "+str(dp.infopacket["unitno"])+" "+str(dp.infopacket["name"]))
          Settings.p2plist.sort(reverse=False,key=self.nodesort)
         else:
          misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Unit alive: "+str(dp.infopacket["unitno"]))
          if Settings.p2plist[un]["type"]==0:
           Settings.p2plist[un]["name"] = dp.infopacket["name"]
           Settings.p2plist[un]["build"] = dp.infopacket["build"]
           Settings.p2plist[un]["type"] = dp.infopacket["type"]
           Settings.p2plist[un]["mac"] = dp.infopacket["mac"]
          Settings.p2plist[un]["cap"] = dp.infopacket["cap"]
          Settings.p2plist[un]["lastseen"] = datetime.now()
          Settings.p2plist[un]["lastrssi"] = self.bleserv.getrssi()

        elif dp.pkgtype==5:                          # process incoming data
          if int(dp.sensordata["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.sensordata["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
           Settings.p2plist[un]["lastrssi"] = self.bleserv.getrssi()
          else:
           Settings.p2plist.append({"protocol":"BLE","unitno":dp.sensordata["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":self.bleserv.getrssi(),"cap":1})

          if (int(Settings.Settings["Unit"])==int(dp.sensordata["dunit"])) or (0==int(dp.sensordata["dunit"])): # process only if we are the destination or broadcast
           ltaskindex = -1
           for x in range(0,len(Settings.Tasks)): # check if the sent IDX already exists?
             try:
              if (type(Settings.Tasks[x]) is not bool and Settings.Tasks[x]):
                if Settings.Tasks[x].controlleridx[self.controllerindex]==int(dp.sensordata["idx"]):
                 ltaskindex = x
                 break
             except Exception as e:
              print(e)
           dvaluecount = int(dp.sensordata["valuecount"])
           if rpieGlobals.VARS_PER_TASK<dvaluecount: # avoid possible buffer overflow
            dvaluecount = rpieGlobals.VARS_PER_TASK
           if ltaskindex < 0: # create new task if necessarry
            devtype = int(dp.sensordata["pluginid"])
            m = False
            try:
             for y in range(len(rpieGlobals.deviceselector)):
              if int(rpieGlobals.deviceselector[y][1]) == devtype:
               m = __import__(rpieGlobals.deviceselector[y][0])
               break
            except:
             m = False
            TempEvent = None
            if m:
             try: 
              TempEvent = m.Plugin(-1)
             except:
              TempEvent = None
            if True:
             ltaskindex = -1
             for x in range(0,len(Settings.Tasks)): # check if there are free TaskIndex slot exists
               try:
                if (type(Settings.Tasks[x]) is bool):
                 if Settings.Tasks[x]==False:
                  ltaskindex = x
                  break
               except:
                pass
             devtype = 33 # dummy device
             m = False
             try:
              for y in range(len(rpieGlobals.deviceselector)):
               if int(rpieGlobals.deviceselector[y][1]) == devtype:
                m = __import__(rpieGlobals.deviceselector[y][0])
                break
             except:
              m = False
             if m:
              if ltaskindex<0:
               ltaskindex = len(Settings.Tasks)
              try:
               Settings.Tasks[ltaskindex] = m.Plugin(ltaskindex)
              except:
               ltaskindex = len(Settings.Tasks)
               Settings.Tasks.append(m.Plugin(ltaskindex))  # add a new device
              Settings.Tasks[ltaskindex].plugin_init(True)
              Settings.Tasks[ltaskindex].remotefeed = True  # Mark that this task accepts incoming data updates!
              Settings.Tasks[ltaskindex].enabled  = True
              Settings.Tasks[ltaskindex].interval = 0
              Settings.Tasks[ltaskindex].senddataenabled[self.controllerindex]=True
              Settings.Tasks[ltaskindex].controlleridx[self.controllerindex]=int(dp.sensordata["idx"])
              if TempEvent is not None:
               Settings.Tasks[ltaskindex].taskname = TempEvent.PLUGIN_NAME.replace(" ","")
               for v in range(dvaluecount):
                Settings.Tasks[ltaskindex].valuenames[v] = TempEvent.valuenames[v]
               Settings.Tasks[ltaskindex].taskdevicepluginconfig[0] = TempEvent.vtype
               Settings.Tasks[ltaskindex].vtype = TempEvent.vtype
              else:
               Settings.Tasks[ltaskindex].taskname = Settings.Tasks[ltaskindex].PLUGIN_NAME.replace(" ","")
              Settings.Tasks[ltaskindex].valuecount = dvaluecount
              Settings.savetasks()
           if ltaskindex<0:
            return False
           misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sensordata update arrived from unit "+str(dp.sensordata["sunit"])) # save received values
           if Settings.Tasks[ltaskindex].remotefeed:
            for v in range(dvaluecount):
             Settings.Tasks[ltaskindex].set_value(v+1,dp.sensordata["values"][v],False)
            Settings.Tasks[ltaskindex].plugin_senddata()
          elif (int(Settings.Settings["Unit"])!=int(dp.sensordata["dunit"])): # reroute if pkt is not for us
            if (self.defaultunit!=int(dp.sensordata["dunit"])) and (self.enablesend or self.directsend): # ... and not came from default target, and sending is enabled
             if self.directsend:
              un = getunitordfromnum(dp.sensordata["dunit"]) # try direct send only if instructed to do so
             else:
              un = -1
             self.bleclient.setdestination(self.defaultdestination)
             if un>-1:
              if (int(Settings.p2plist[un]["cap"]) & 2)==2: # try only if endpoint is able to receive
               self.bleclient.setdestination(Settings.p2plist[un]["mac"])
             success = self.bleclient.send(dp.buffer)
             if success==False and un>-1:
              self.bleclient.setdestination(self.defaultdestination)
              success = self.bleclient.send(dp.buffer)

        elif dp.pkgtype==7: # process incoming command
          if int(dp.cmdpacket["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.cmdpacket["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
           Settings.p2plist[un]["lastrssi"] = self.bleserv.getrssi()
          else:
           Settings.p2plist.append({"protocol":"BLE","unitno":dp.cmdpacket["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":self.bleserv.getrssi(),"cap":1})
          if (int(Settings.Settings["Unit"])==int(dp.cmdpacket["dunit"])) or (0==int(dp.cmdpacket["dunit"])): # process only if we are the destination or broadcast
           misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Command arrived from "+str(dp.cmdpacket["sunit"]))
#           print(dp.cmdpacket["cmdline"]) # DEBUG
           commands.doExecuteCommand(dp.cmdpacket["cmdline"],True)


 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if self.enabled and self.initialized:
#   print(idx,value) # debug
   if int(idx)>0:
    if Settings.Tasks[tasknum].remotefeed == False:  # do not republish received values
     dp2 = p2pbuffer.data_packet()
     dp2.sensordata["sunit"] = Settings.Settings["Unit"]
     dp2.sensordata["dunit"] = self.defaultunit
     dp2.sensordata["idx"] = idx
     if tasknum>-1:
      dp2.sensordata["pluginid"] = Settings.Tasks[tasknum].pluginid
     else:
      dp2.sensordata["pluginid"] = 33
     dp2.sensordata["valuecount"] = Settings.Tasks[tasknum].valuecount
     for u in range(Settings.Tasks[tasknum].valuecount):
      dp2.sensordata["values"][u] = Settings.Tasks[tasknum].uservar[u]
     dp2.encode(5)
#     print(dp2.buffer) # debug
     if self.directsend:
      un = getunitordfromnum(self.defaultunit) # try direct send only if instructed to do so
     else:
      un = -1
     self.bleclient.setdestination(self.defaultdestination)
     if un>-1:
      if (int(Settings.p2plist[un]["cap"]) & 2)==2: # try only if endpoint is able to receive
       self.bleclient.setdestination(Settings.p2plist[un]["mac"])
 #      print("a2:",Settings.p2plist[un]["mac"])
     success = self.bleclient.send(dp2.buffer)
     if success==False and un>-1:
#      print("retry",success,un) # debug
      self.bleclient.setdestination(self.defaultdestination)
      success = self.bleclient.send(dp2.buffer)
     return success

 def sendcommand(self,unitno,commandstr):
     dpc = p2pbuffer.data_packet()
     dpc.cmdpacket["sunit"] = Settings.Settings["Unit"]
     dpc.cmdpacket["dunit"] = unitno
     dpc.cmdpacket["cmdline"] = commandstr
     dpc.encode(7)
     un = getunitordfromnum(unitno) # try direct send anyway
     if un==-1:
      self.bleclient.setdestination(self.defaultdestination)
     else:
      self.bleclient.setdestination(Settings.p2plist[un]["mac"])
     success = self.bleclient.send(dpc.buffer)
     if success==False and un>-1:
      self.bleclient.setdestination(self.defaultdestination)
      success = self.bleclient.send(dpc.buffer)
     return success

 def timer_thirty_second(self):
  if self.enabled and self.initialized:
   if self.defaultdestination!="" and ((time.time()-self.lastsysinfo) >self.sysinfoperiod):
    dp = p2pbuffer.data_packet()
    try:
     dp.infopacket["mac"] = self.bleserv.getaddress()
    except Exception as e:
     dp.infopacket["mac"] = "00:00:00:00:00:00"
    dp.infopacket["unitno"] = int(Settings.Settings["Unit"])
    dp.infopacket["build"] = int(rpieGlobals.BUILD)
    dp.infopacket["name"] = Settings.Settings["Name"]
    dp.infopacket["type"] = int(rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD)
    # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
    dp.infopacket["cap"] = self.getmode()
    dp.encode(1)
    self.bleclient.setdestination(self.defaultdestination)
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sending infopacket")
    success = False
    if self.bleclient.connect():
        success = self.bleclient.writepayload(dp.buffer)
        reply = self.bleclient.readpayload() # read remote infos
        self.bleclient.disconnect()
        if reply:
         self.pkt_receiver(reply) # handle received infos
    if success:
     self.lastsysinfo = time.time()
    else:
     self.lastsysinfo = (time.time()-self.sysinfoperiod)+10 # retry in 10sec
  return True

 def getmode(self):
    wm = 0
    if self.enablesend or self.directsend:
     wm = 1
    if self.enablerec:
     wm += 2
    return wm

class InfoCharacteristic(Characteristic):
    def __init__(self,addressfunc=None,modefunc=None):
        Characteristic.__init__(self, {
            'uuid': BLE_INFO_CHAR,
            'properties': ['read'],
            'descriptors': [
                    Descriptor({
                        "uuid" : "2901",
                        "value" : array.array('B',[73, 110, 102, 111, 32, 112, 97, 99, 107, 101, 116])}
                    )],
            'value': None
          })
        self._value = []
        self.addressfunc=addressfunc
        self.modefunc=modefunc

    def onReadRequest(self, offset, callback):
      dp = p2pbuffer.data_packet()
      try:
       dp.infopacket["mac"] = self.addressfunc()
      except Exception as e:
       dp.infopacket["mac"] = "00:00:00:00:00:00"
      dp.infopacket["unitno"] = int(Settings.Settings["Unit"])
      dp.infopacket["build"] = int(rpieGlobals.BUILD)
      dp.infopacket["name"] = Settings.Settings["Name"]
      dp.infopacket["type"] = int(rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD)
      # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
      dp.infopacket["cap"] = self.modefunc()
      dp.encode(1)
#      data = array.array('B',[0]*64)
      data = list(dp.buffer)
#      print(offset,data[offset:])
      callback(Characteristic.RESULT_SUCCESS, data[offset:])

class ReceiverCharacteristic(Characteristic):
    def __init__(self, updateValueCallback=None):
        Characteristic.__init__(self, {
            'uuid': BLE_RECEIVER_CHAR,
            'properties': ['write'],
            'descriptors': [
                    Descriptor({
                        "uuid" : '2901',
                        "value" : array.array('B',[80, 50, 80, 32, 109, 101, 115, 115, 97, 103, 101, 32, 113, 117, 101, 117, 101])}
                    )],
            'value': None
          })
        self._value = []
        self._updateValueCallback = updateValueCallback

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        self._value = data
#        print('EchoCharacteristic - %s - onWriteRequest: value = %s' % (self['uuid'], [hex(c) for c in self._value]))
        if self._updateValueCallback:
            self._updateValueCallback(self._value)
        callback(Characteristic.RESULT_SUCCESS)

class RPIBLEService(BlenoPrimaryService):
    def __init__(self,s_updateValueCallback=None,nameval="",addrfunc=None,mfunc=None):
        BlenoPrimaryService.__init__(self, {
          'uuid': BLE_SERVICE_ID,
          'characteristics': [
              ReceiverCharacteristic(updateValueCallback=s_updateValueCallback),
              InfoCharacteristic(addressfunc=addrfunc,modefunc=mfunc)
          ]})

class BLEServer():
    def __init__(self, name="",receiverfunc=None,pmodefunc=None):
        self.receiverfunc=receiverfunc
        self.name    = name
        self.bleno   = None
        self.service = None
        self.initialized = False
        self.address = ""
        self.modefunc=pmodefunc

    def start(self):
        self.address = ""
        self.bleno = Bleno()
        self.service = RPIBLEService(self.receiverfunc,self.name,self.getaddress,self.modefunc)
        self.bleno.on('stateChange', self.onStateChange)
        self.bleno.on('advertisingStart', self.onAdvertisingStart)
        self.bleno.start()
        self.initialized = True

    def getrssi(self):
        return self.bleno.rssi

    def getaddress(self):
        if self.bleno is None:
         self.bleno = Bleno()
        if self.bleno is not None:
         if self.address == "":
          try:
            if self.bleno.address is not None and self.bleno.address != "" and self.bleno.address != "unknown":
             self.address = self.bleno.address
            else:
             self.bleno._bindings._hci.init()
             self.bleno._bindings._hci.readBdAddr() # force read BT address cmd
             time.sleep(0.5)
             self.address = self.bleno._bindings._hci.address
            aa = self.address.split(":")
            self.address = ""
            for l in reversed(range(len(aa))):
             self.address += aa[l]+":"
            self.address = self.address[:-1]
          except Exception as e:
            print(e)
         return self.address
        else:
         return ""

    def onStateChange(self,state):
#      print('on -> stateChange: ' + state);
      if (state == 'poweredOn'):
       self.bleno.startAdvertising(self.name, [BLE_SERVICE_ID]);
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"BLE Service started at: "+str(self.getaddress()))
      else:
       self.bleno.stopAdvertising();

    def onAdvertisingStart(self,error):
#     print('on -> advertisingStart: ' + ('error ' + error if error else 'success'));
     if not error:
        def on_setServiceError(error):
          if error:
             misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE service start: "+str(error))
#            print('setServices: %s'  % ('error ' + error if error else 'success'))
        self.bleno.setServices([
            self.service
        ], on_setServiceError)
     else:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BLE advertising result: "+str(error))

    def stop(self):
     self.bleno.stopAdvertising()
     self.bleno.disconnect()

class BLEClient():
    def __init__(self,address="",duty=0):
        self.address=address
        self.tx_active = False
        self.tx_start  = 0
        self.tx_end    = 0
        self.nexttransmit = 0
        self.duty=duty
        self.service = None
        self.periph  = None

    def setdestination(self,address):
        self.address=address.lower().strip() # only lower case address is supported by BluePy!!

    def connect(self):
       if self.tx_active or self.address=="":
        return False
       self.tx_start = millis()
       if self.tx_start<self.nexttransmit:
        print("Next possible transmit ",self.nexttransmit)
        return False
       self.tx_active = True
       try:
        self.periph = Peripheral(self.address)
       except Exception as e: 
#        print("connect error",e)
        self.tx_active = False
        self.tx_end = millis()
        return False
       try:
        self.service = self.periph.getServiceByUUID(BLE_SERVICE_ID)
       except Exception as e:
#        print("service error ",e)
        self.tx_active = False
        self.tx_end = millis()
        return False
       return True

    def writepayload(self,apayload):
       try:
        ch = self.service.getCharacteristics(BLE_RECEIVER_CHAR)[0]
#        print(ch,apayload,len(apayload))
        ch.write(apayload, True)
       except Exception as e:
#        print("write error ",e)
        return False
       return True

    def readpayload(self):
       payload = []
       try:
        ch = self.service.getCharacteristics(BLE_INFO_CHAR)[0]
        payload = ch.read()
       except Exception as e:
#        print("read error ",e)
        pass
       return payload

    def disconnect(self):
       try:
        self.periph.disconnect()
       except:
        return False
       self.tx_active = False
       self.tx_end = millis()
       if self.duty>0:
        self.nexttransmit = ((self.tx_end-self.tx_start)*self.duty)+self.tx_end
       return True

    def send(self,spayload):
       if self.connect():
        self.writepayload(spayload)
        self.disconnect()

# Helper functions

def getunitordfromnum(unitno):
  for n in range(len(Settings.p2plist)):
   if int(Settings.p2plist[n]["unitno"]) == int(unitno) and str(Settings.p2plist[n]["protocol"]) == "BLE":
    return n
  return -1

