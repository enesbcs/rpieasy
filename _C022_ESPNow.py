#!/usr/bin/env python3
#############################################################################
##################### ESPNow controller for RPIEasy #########################
#############################################################################
#
# This controller is able to send and receive data through ESPNow using a
# serially connected ESP8266.
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
import threading
import serial
import lib.lib_serial as rpiSerial

CAPABILITY_BYTE = (1+2) # send and receive

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 22
 CONTROLLER_NAME = "ESPNow (EXPERIMENTAL)"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = True
  self.onmsgcallbacksupported = False # use direct set_value() instead of generic callback to make sure that values setted anyway
  self.controllerport = 1
  self.lastsysinfo = 0
  self.sysinfoperiod = 180 # seconds
  self.timer30s = True
  self.defaultunit = 0
  self.enablesend = True
  self.bsize = 8
  self.sbit  = 1
  self.baud  = 115200
  self.bgproc = None
  self.serdev = None
  self.timeout = 0.001
  self.maxexpecteddata = 512
  self.port = ""
  self.mac  = ""
  self.wchan = 1
  self.connected = False

 def calctimeout(self):
  try:
   if self.baud<50:
    self.baud = 50
  except:
   self.baud = 50
  if self.maxexpecteddata>4096:# Linux serial buffer is fixed max 4096 bytes
   self.maxexpecteddata=4096
  if self.maxexpecteddata<1:
   self.maxexpecteddata=1
  self.timeout = (self.bsize+self.sbit)*self.maxexpecteddata/self.baud

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.initialized = False
  try:
   if str(self.port)!="0" and str(self.port).strip()!="" and self.baud != 0:
    self.initialized = False
    if self.enabled:
     if int(Settings.Settings["Unit"])>0:
      self.controllerport = Settings.Settings["Unit"]
     self.calctimeout()
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Try to init serial "+str(self.port)+" speed "+str(self.baud))
     self.enabled = False
     self.connect()
     time.sleep(3)
     self.enabled = True

     if self.connected:
      self.initialized = True
      misc.shadowlogenabled = True
      self.bgproc = threading.Thread(target=self.bgreceiver)
      self.bgproc.daemon = True
      self.bgproc.start()
      time.sleep(2)
      mode = self.changemode(0)
      if mode!=0:
       mode = self.changemode(0)
      if mode!=0:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Serial ESPNow GW adapter is not compatible!")
       self.initialized = False
       self.disconnect()

     if self.connected:
      if int(self.controllerport)>0:
       self.serialcommand("unit,"+str(self.controllerport))
      time.sleep(0.2)
      self.serialcommand("espnow,dest,"+str(self.defaultunit))
      time.sleep(0.2)
      self.serialcommand("espnow,chan,"+str(self.wchan))
      time.sleep(0.2)
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Serial ESPNow GW initialized")
      self.serialcommand("settings")
      time.sleep(0.5)
      scmdarr = getlastseriallogs(3)
      sreading = ""
      for i in range(len(scmdarr)):
       if "MAC" in scmdarr[i]:
        sreading = scmdarr[1].replace("SERIAL: ","").strip()
        break
      if "MAC" in sreading:
       ms = sreading.split(":")
       sreading = ""
       for i in range(1,len(ms)):
        sreading += ms[i].strip()
        if i!=len(ms)-1:
         sreading += ":"
       self.mac = sreading.strip()
      else:
       try:
        defdev = Settings.NetMan.getprimarydevice()
       except:
        defdev = -1
       if defdev != -1:
        self.mac = Settings.NetworkDevices[defdev].mac
       else:
        self.mac = "00:00:00:00:00:00"
#      print(self.mac)
    else:
     self.baud = 0
     try:
      self.serdev.close() # close in case if already opened by ourself
     except:
      pass
  except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
  return True

 def connect(self):
    self.connected = False
    self.lastsysinfo = 0
    try:
     self.serdev.close() # close in case if already opened by ourself
    except:
     pass
    try:
     self.serdev = rpiSerial.SerialPort(self.port,self.baud,ptimeout=self.timeout,pbytesize=self.bsize,pstopbits=self.sbit)
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Serial connected "+str(self.port))
     self.connected = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Serial failed "+str(e))
    try:
     self.connected = self.serdev.isopened()
    except Exception as e:
     self.connected = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Open failed "+str(e))

 def changemode(self,modenum):
      result = -1
      self.serialcommand("espnow,mode,"+str(modenum)) # TRY TO SET MODE
      time.sleep(0.5)
      scmdarr = getlastseriallogs(3)
      if len(scmdarr)>2:
       if "espnow,mode" in scmdarr[2]:
        result = scmdarr[1].replace("SERIAL: ","").strip()
        try:
         result = int(result)
        except:
         result = -1
      return result

 def disconnect(self):
  self.connected = False
  try:
     self.serdev.close() # close in case if already opened by ourself
  except:
     pass

 def webform_load(self):
  webserver.addFormNote("IP and Port parameter is not used!")
  try:
   choice1 = self.port
   options = rpiSerial.serial_portlist()
   if len(options)>0:
    webserver.addHtml("<tr><td>Serial Device:<td>")
    webserver.addSelector_Head("ser_addr",False)
    for o in range(len(options)):
     webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
    webserver.addSelector_Foot()
    webserver.addFormNote("For RPI use 'raspi-config' tool: 5- Interfacing Options-P6 Serial- (Kernel logging disabled + serial port hardware enabled) before enable this plugin")
    webserver.addFormNumericBox("Baudrate","ser_spd",self.baud,50,4000000)
    webserver.addFormNote("Generic values: 9600, 19200, 38400, 57600, 115200")
#    webserver.addFormCheckBox("Enable Sending","sender",self.enablesend)
    webserver.addFormNumericBox("Default destination node index","defaultnode",self.defaultunit,0,255)
    webserver.addFormNote("Default node index for data sending")
    webserver.addFormNote("Detected gateway MAC address "+str(self.mac))
    options = []
    optionvalues = []
    for i in range(1,14):
       options.append(str(i))
       optionvalues.append(i)
    webserver.addFormSelector("Wifi channel","wchannel",len(options),options,optionvalues,None,self.wchan)
    webserver.addFormNote("Set the same wifi channel at all nodes!")
    webserver.addWideButton("espnow","ESPNow endpoint management","")
   else:
    webserver.addFormNote("No serial ports found")

  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ESPNow GW init error: "+str(e))
  return True

 def webform_save(self,params):
  try:
   self.port = str(webserver.arg("ser_addr",params))
   self.baud = int(webserver.arg("ser_spd",params))
   self.wchan = int(webserver.arg("wchannel",params))
   self.defaultunit = int(webserver.arg("defaultnode",params))
#   self.enablesend = (webserver.arg("sender",params)=="on")
  except Exception as e:
   self.baud = 0
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ESPNow parameter save: "+str(e))
  self.calctimeout()
  return True

 def nodesort(self,item):
  v = 0
  try:
   v = int(item["unitno"])
  except:
   v = 0
  return v

 def bgreceiver(self):
  if self.initialized:
   while self.enabled:
    if self.serdev is not None:
#     tt = rpieTime.millis()
     try:
      while self.serdev.available()>0:
       reading = self.serdev.readline()
       if len(reading)>0:
        if reading[0]==255:
         self.pkt_receiver(reading)
        else:
         sstr = str(reading.decode("utf-8")).strip()
         if sstr != "":
          misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"SERIAL: "+sstr)
     except Exception as e:
      time.sleep(0.2)
    time.sleep(0.005)
   try:
     self.serdev.close()
   except:
     pass

 def pkt_receiver(self,payload):
  if self.enabled:
   while len(payload)>0:
    dp = p2pbuffer.data_packet()
    dp.buffer = payload
    dp.decode()
#    print(dp.pktlen,dp.pkgtype)
#    print("DATA ARRIVED ",payload,dp.buffer)
    if int(dp.pkgtype)!=0:
        if dp.pkgtype==1:
         if int(dp.infopacket["unitno"]) == int(Settings.Settings["Unit"]): # skip own messages
          return False
         un = getunitordfromnum(dp.infopacket["unitno"]) # process incoming alive reports
         if un==-1:
          # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
          Settings.p2plist.append({"protocol":"ESPNOW","unitno":dp.infopacket["unitno"],"name":dp.infopacket["name"],"build":dp.infopacket["build"],"type":dp.infopacket["type"],"mac":dp.infopacket["mac"],"lastseen":datetime.now(),"lastrssi":"","cap":dp.infopacket["cap"]})
          misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"New ESPNOW unit discovered: "+str(dp.infopacket["unitno"])+" "+str(dp.infopacket["name"]))
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

        elif dp.pkgtype==5:                          # process incoming data
          if int(dp.sensordata["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.sensordata["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
          else:
           Settings.p2plist.append({"protocol":"ESPNOW","unitno":dp.sensordata["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":"","cap":1})

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
              Settings.Tasks[ltaskindex].remotefeed = int(dp.sensordata["sunit"]) # True  # Mark that this task accepts incoming data updates!
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

        elif dp.pkgtype==7: # process incoming command
          if int(dp.cmdpacket["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.cmdpacket["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
          else:
           Settings.p2plist.append({"protocol":"ESPNOW","unitno":dp.cmdpacket["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":"","cap":1})
          if (int(Settings.Settings["Unit"])==int(dp.cmdpacket["dunit"])) or (0==int(dp.cmdpacket["dunit"])): # process only if we are the destination or broadcast
           misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Command arrived from "+str(dp.cmdpacket["sunit"]))
           commands.doExecuteCommand(dp.cmdpacket["cmdline"],True)

        elif dp.pkgtype==8: # process incoming text/log
          if int(dp.cmdpacket["sunit"])==int(Settings.Settings["Unit"]):
           return False
          un = getunitordfromnum(dp.cmdpacket["sunit"])
          if un>-1: # refresh lastseen data
           Settings.p2plist[un]["lastseen"] = datetime.now()
          else:
           Settings.p2plist.append({"protocol":"ESPNOW","unitno":dp.cmdpacket["sunit"],"name":"","build":0,"type":0,"mac":"","lastseen":datetime.now(),"lastrssi":"","cap":1})
          if (int(Settings.Settings["Unit"])==int(dp.cmdpacket["dunit"])) or (0==int(dp.cmdpacket["dunit"])): # process only if we are the destination or broadcast
           misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"ESPNOW: "+str(dp.cmdpacket["cmdline"]))

        payload = payload[dp.pktlen:-1]
    else:
     payload = payload[1:-1]


 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if self.enabled and self.initialized and self.enablesend:
   if int(idx)>0:
    if int(Settings.Tasks[tasknum].remotefeed) < 1:  # do not republish received values
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
     if self.serdev is not None:
      try:
       self.serdev.write(dp2.buffer)
      except Exception as e:
       print(e)

 def sendcommand(self,unitno,commandstr):
  if self.enabled and self.initialized and self.enablesend:
     dpc = p2pbuffer.data_packet()
     dpc.cmdpacket["sunit"] = Settings.Settings["Unit"]
     dpc.cmdpacket["dunit"] = unitno
#     print("CMD:",commandstr)
     dpc.cmdpacket["cmdline"] = commandstr
     dpc.encode(7)
#     print("RPIEasy buffer:",dpc.buffer) # debug
     if self.serdev is not None:
      try:
       self.serdev.write(dpc.buffer)
      except Exception as e:
       print(e)

 def timer_thirty_second(self):
  if self.enabled and self.initialized and ((time.time()-self.lastsysinfo) >self.sysinfoperiod):
   self.sendsysinfo()

 def sendsysinfo(self):
  if self.enabled and self.initialized and self.enablesend:
    dp = p2pbuffer.data_packet()
    dp.infopacket["mac"] = self.mac
    dp.infopacket["unitno"] = int(Settings.Settings["Unit"])
    dp.infopacket["build"] = int(rpieGlobals.BUILD)
    dp.infopacket["name"] = Settings.Settings["Name"]
    dp.infopacket["type"] = int(rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD)
    # CAPABILITIES byte: first bit 1 if able to send, second bit 1 if able to receive
    dp.infopacket["cap"] = int(CAPABILITY_BYTE)
    dp.encode(1)
#    print(dp.buffer) # debug
    self.lastsysinfo = time.time()
    return True
  return False

 def serialcommand(self,cmd):
   if self.serdev is not None:
    try:
     while self.serdev.available()>0:
       reading = self.serdev.readline()
     self.serdev.write(cmd+'\n')
    except Exception as e:
     pass

# Helper functions

def getunitordfromnum(unitno):
  for n in range(len(Settings.p2plist)):
   if int(Settings.p2plist[n]["unitno"]) == int(unitno) and str(Settings.p2plist[n]["protocol"]) == "ESPNOW":
    return n
  return -1

def getlastseriallogs(num=3):
    scmdarr = []
    for i in reversed(range(len(misc.ShadowLog))):
     if len(scmdarr)>=num:
      break
     if misc.ShadowLog[i]["lvl"]== rpieGlobals.LOG_LEVEL_DEBUG:
      if "SERIAL:" in misc.ShadowLog[i]["l"]:
       scmdarr.append(misc.ShadowLog[i]["l"].replace("SERIAL:","").strip())
    return scmdarr

def getlastespnowlogs(num=1):
    scmdarr = []
    for i in reversed(range(len(misc.ShadowLog))):
     if len(scmdarr)>=num:
      break
     if misc.ShadowLog[i]["lvl"]== rpieGlobals.LOG_LEVEL_DEBUG:
      if "ESPNOW:" in misc.ShadowLog[i]["l"]:
       scmdarr.append(misc.ShadowLog[i]["l"].replace("ESPNOW:","").strip())
    return scmdarr

############################
## WEBSERVER PART FOLLOWS ##
############################

@webserver.WebServer.route('/espnow')
def handle_espnow(self):
  try:
   webserver.TXBuffer=""
   if self.type == "GET":
    responsearr = self.get
   else:
    responsearr = self.post

   try:
    managenode = webserver.arg('nodenum',responsearr)
   except:
    managenode = ""

   try:
    tasknum = int(webserver.arg('tasknum',responsearr))
   except:
    tasknum = 0

   taskmode = False
   i2cmode  = False
   for i in range(1,48):
    try:
     if webserver.arg('del'+str(i),responsearr) != '':
      if str(managenode)=="local":
       commands.doExecuteCommand("serialcommand,taskclear,"+str(i),False)
       taskmode = True
       break
      elif str(managenode)!="":
       commands.doExecuteCommand("espnowcommand,"+str(managenode)+",taskclear,"+str(i),False)
       taskmode = True
       time.sleep(1)
       break
    except:
     pass

   if int(tasknum)>0:
      taskc = ["Conf",tasknum,0,0,0,0,0,0,0,0,0,0]
      taska = ["Task",tasknum,0,-1,-1,-1,0,0,0]
      wv = -1
      try:
       wv = int(webserver.arg('pluginid',responsearr))
      except:
       wv = -999
      if wv > -999:
       taska[2] = wv
      for i in range(1,4):
       try:
        wv = int(webserver.arg('pin'+str(i),responsearr))
       except:
        wv = -999
       if wv>-999:
        taska[2+i]=wv
      try:
       wv = int(webserver.arg('interval',responsearr))
      except:
       wv = -999
      if wv>-999:
       taska[7] = wv
      try:
       wv = int(webserver.arg('idx',responsearr))
      except:
       wv = -999
      if wv>-999:
       taska[8] = wv
      try:
       wv = int(webserver.arg('port',responsearr))
      except:
       wv = -999
      if wv>-999:
       taska[6] = wv
      try:
       wv = webserver.arg('pullup',responsearr)
       if str(wv)=="on":
        wv = 1
       else:
        wv = 0
      except:
       wv = 0
      if wv>-1:
       taskc[2] = wv
      try:
       wv = webserver.arg('inverse',responsearr)
       if str(wv)=="on":
        wv = 1
       else:
        wv = 0
      except:
       wv = 0
      if wv>-1:
       taskc[3] = wv
      for i in range(0,8):
       try:
        wv = webserver.arg('c'+str(i),responsearr)
        wv = int(wv)
       except:
        if str(wv)=="on":
         wv = 1
        else:
         wv = 0
       if wv>-1:
        taskc[4+i]=wv
      if str(managenode)=="local":
       tcmd = "serialcommand,"
      else:
       tcmd = "espnowcommand,"+str(managenode)+","
      tcmdc = tcmd + "espnow,taskconf"
      tcmda = tcmd + "espnow,taskadd"
      for i in range(1,len(taskc)):
       tcmdc += ","+str(taskc[i])
      for i in range(1,len(taska)):
       tcmda += ","+str(taska[i])
      commands.doExecuteCommand(tcmdc,False)
      time.sleep(1)
      commands.doExecuteCommand(tcmda,False)
#      print(tcmdc)
#      print(tcmda)
      taskmode = True
   elif taskmode==False:
    for i in range(1,48):
     try:
      if webserver.arg('add'+str(i),responsearr) != '':
       tasknum = i
       taskmode = True
       taskc = ["Conf",i,0,0,0,0,0,0,0,0,0,0]
       taska = ["Task",i,0,-1,-1,-1,0,0,0]
       break
     except:
      pass


   if taskmode:
    pass

   elif ( (webserver.arg('savelocal',responsearr) != '') or (webserver.arg('savenode',responsearr) != '') ):
    try:
       workmode = int(webserver.arg('workmode',responsearr))
    except:
       workmode = 0
    try:
       nodenum = int(webserver.arg('nnodenum',responsearr))
    except:
       nodenum = 0
    try:
       dnodenum = int(webserver.arg('dnodenum',responsearr))
    except:
       dnodenum = 0
    try:
       name = str(webserver.arg('name',responsearr))
    except:
       name = ""
    try:
       wchannel = int(webserver.arg('wchannel',responsearr))
    except:
       wchannel = 1
    try:
       deepsleep = int(webserver.arg('deepsleep',responsearr))
    except:
       deepsleep = 1
    if str(managenode)=="local":
       tcmd = "serialcommand,"
       dt = 0.5
    elif str(managenode)!="":
       tcmd = "espnowcommand,"+str(managenode)+","
       dt = 2
    commands.doExecuteCommand(tcmd+"espnow,mode,"+str(workmode),False)
    time.sleep(dt)
    commands.doExecuteCommand(tcmd+"espnow,name,"+str(name),False)
    time.sleep(dt)
    commands.doExecuteCommand(tcmd+"espnow,deepsleep,"+str(deepsleep),False)
    time.sleep(dt)
    commands.doExecuteCommand(tcmd+"espnow,chan,"+str(wchannel),False)
    time.sleep(dt)
    commands.doExecuteCommand(tcmd+"espnow,dest,"+str(dnodenum),False)
    time.sleep(dt)
    commands.doExecuteCommand(tcmd+"unit,"+str(nodenum),False)
    time.sleep(dt)
    if str(managenode)=="local":
       pass
    elif str(managenode)!="":
       commands.doExecuteCommand(tcmd+"reboot",False) # just for sure reboot old node
       commands.doExecuteCommand("espnowcommand,"+str(nodenum)+",reboot",False) # reboot new node number
    time.sleep(dt*3)
    managenode = "" # return to main page instead of re-request all settings

   elif webserver.arg('submit',responsearr) != '':
    pass

   elif webserver.arg('search',responsearr) != '':
    commands.doExecuteCommand("espnowcommand,0,espnow,sendinfo",False) # broadcast command to every node
    managenode = ""

   elif webserver.arg('reboot',responsearr) != '':
    if str(managenode)!="local" and str(managenode)!="":
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",reboot",False) # reboot selected node
    else:
     commands.doExecuteCommand("serialcommand,reboot",False) # reboot selected node
    managenode = ""

   elif webserver.arg('i2c',responsearr) != '':
    i2cmode = True

   elif webserver.arg('tasks',responsearr) != '':
    taskmode = True

   elif webserver.arg('time',responsearr) != '':
    if str(managenode)=="local":
     commands.doExecuteCommand("serialcommand,espnow,setdate,"+datetime.now().strftime('%Y,%m,%d,%H,%M,%S'),False)
    elif str(managenode)!="":
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,setdate,"+datetime.now().strftime('%Y,%m,%d,%H,%M,%S'),False)
    managenode = ""

   webserver.sendHeadandTail("TmplStd",webserver._HEAD)

   if i2cmode:
    webserver.TXBuffer += "<form name='frmadd' method='post'><table class='normal'>"
    webserver.addFormHeader("I2C scan on Node "+str(managenode))
    if str(managenode)=="local":
     commands.doExecuteCommand("serialcommand,i2cscanner",False)
     time.sleep(1)
    elif str(managenode)!="":
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",i2cscanner",False)
     time.sleep(3)
    scmdarr = []
    for i in reversed(range(len(misc.ShadowLog))):
      if len(scmdarr)>=30:
       break
      if "i2cscanner" in misc.ShadowLog[i]["l"]:
       break
      if misc.ShadowLog[i]["lvl"]== rpieGlobals.LOG_LEVEL_DEBUG:
       if "I2C  :" in misc.ShadowLog[i]["l"]:
        scmdarr.append(misc.ShadowLog[i]["l"].replace("ESPNOW:","").replace("SERIAL:","").strip())
    webserver.TXBuffer += "<TR><TD colspan='2'><textarea readonly rows='10' wrap='on'>"
    for i in range(len(scmdarr)):
     webserver.TXBuffer += scmdarr[i]+"&#13;&#10;"
    webserver.TXBuffer += "</textarea><br>"
    webserver.addButton("espnow","Back")
    webserver.TXBuffer += "</table></form>"
    webserver.sendHeadandTail("TmplStd",webserver._TAIL)
    return webserver.TXBuffer

   elif taskmode and int(tasknum)>0: # display plugin selection
    webserver.TXBuffer += "<form name='frmadd' method='post'><table class='normal'>"
    webserver.addFormHeader("ESPNow add new task "+str(tasknum)+" on Node "+str(managenode))
    displaytask(taska,taskc)
    webserver.addHtml("<tr><td><input type='hidden' name='nodenum' value='"+str(managenode)+"'><input type='hidden' name='tasknum' value='"+str(tasknum)+"'>")
    webserver.addSubmitButton("Save task", "savetask")
    webserver.addButton("espnow","Back")

    webserver.TXBuffer += "</table></form>"
    webserver.sendHeadandTail("TmplStd",webserver._TAIL)
    return webserver.TXBuffer

   elif taskmode and str(managenode)!="": # display tasklist
    webserver.TXBuffer += "<form name='frmtask' method='post'><table class='normal'>"
    webserver.addFormHeader("ESPNow tasklist")
    tasks = []
    confs = []
    if str(managenode)=="local": #serial node
     webserver.addFormHeader("Serial node")
     commands.doExecuteCommand("serialcommand,espnow,tasklist",False)
     time.sleep(3)
     scmdarr = getlastseriallogs(30)
    else: # espnow node
     webserver.addFormHeader("Node: "+str(managenode))
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,tasklist",False)
     time.sleep(3)
     scmdarr = []
     for i in reversed(range(len(misc.ShadowLog))):
      if len(scmdarr)>=30:
       break
      if "espnow,tasklist" in misc.ShadowLog[i]["l"]:
       break
      if misc.ShadowLog[i]["lvl"]== rpieGlobals.LOG_LEVEL_DEBUG:
       if "ESPNOW:" in misc.ShadowLog[i]["l"]:
        scmdarr.append(misc.ShadowLog[i]["l"].replace("ESPNOW:","").strip())
    if len(scmdarr)>0:
      for i in range(len(scmdarr)):
       if ",tasklist" in scmdarr[i]:
        break
       if "Task," in scmdarr[i]:
        tasks.append(scmdarr[i])
       elif "Conf," in scmdarr[i]:
        confs.append(scmdarr[i])
    tasknum = 0
    if len(tasks)>0:
     for i in reversed(range(len(tasks))):
      tasknum = len(tasks)-i
      webserver.addFormSubHeader("Task "+str(tasknum))
      webserver.addSubmitButton("Delete task "+str(tasknum), "del"+str(tasknum))
      displaytask(tasks[i],confs[i])
      webserver.addFormSeparator(2)
    webserver.addHtml("<tr><td><input type='hidden' name='nodenum' value='"+str(managenode)+"'>")
    webserver.addSubmitButton("Add new task "+str(tasknum+1), "add"+str(tasknum+1))

    webserver.addButton("espnow","Back")
    webserver.TXBuffer += "</table></form>"
    webserver.sendHeadandTail("TmplStd",webserver._TAIL)
    return webserver.TXBuffer

   elif str(managenode)=="": #  display node list
    webserver.addFormHeader("ESPNow node list")
    webserver.TXBuffer += "<form name='frmespnow' method='post'><table class='multirow'><TR><TH>Select<TH>P2P node number<TH>Name<TH>Build<TH>Type<TH>MAC<TH>Last seen<TH>Capabilities"
    webserver.TXBuffer += "<TR>"
    webserver.TXBuffer += "<td><input type='radio' name='nodenum' value='local'>"
    webserver.TXBuffer +="<TD>serial<TD>local node<TD></TR>"
    if len(Settings.p2plist)>0:
     for n in Settings.p2plist:
      if str(n["protocol"]) == "ESPNOW":
       webserver.TXBuffer += "<TR>"
       webserver.TXBuffer += "<td><input type='radio' name='nodenum' value='"+ str(n["unitno"])+"'>"
       webserver.TXBuffer +="<TD>Unit "+str(n["unitno"])+"<TD>"+str(n["name"])+"<TD>"+str(n["build"])+"<TD>"
       ntype = "Unknown"
       if int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASY_STD:
        ntype = "ESP Easy"
       elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASYM_STD:
        ntype = "ESP Easy Mega"
       elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ESP_EASY32_STD:
        ntype = "ESP Easy32"
       elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ARDUINO_EASY_STD:
        ntype = "Arduino Easy"
       elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_NANO_EASY_STD:
        ntype = "Nano Easy"
       elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD:
        ntype = "RPI Easy"
       elif int(n["type"])==rpieGlobals.NODE_TYPE_ID_ATMEGA_EASY_LORA:
        ntype = "LoRa32u4"
       webserver.TXBuffer += ntype
       webserver.TXBuffer += "<TD>"+str(n["mac"])
       ldt = n["lastseen"]
       lstr = ""
       try:
        lstr = ldt.strftime('%Y-%m-%d %H:%M:%S')
       except:
        lstr = str(ldt)
       webserver.TXBuffer += "<TD>"+lstr
       wm = int(n["cap"])
       wms = ""
       if (wm & 1)==1:
        wms = "SEND "
       if (wm & 2)==2:
        wms += "RECEIVE "
       webserver.TXBuffer += "<TD>"+wms

    webserver.TXBuffer += "</table><br>"
    webserver.addSubmitButton("Manage selected node", "submit")
    webserver.addSubmitButton("Tasks on selected node", "tasks")
    webserver.addSubmitButton("I2C scan selected node", "i2c")
    webserver.addSubmitButton("Reboot selected node", "reboot")
    webserver.addSubmitButton("Set date and time on selected node", "time")
    webserver.TXBuffer += "<P>"
    webserver.addSubmitButton("Request all nodes to advertise itself", "search")
    webserver.TXBuffer += "<P>"
    webserver.addButton("espnow","Refresh")
    webserver.TXBuffer += "</form>"
   elif str(managenode)=="local": # display local settings page
    webserver.addFormHeader("Serial node management")
    webserver.TXBuffer += "<form name='manespnow' method='post'><table class='multirow'>"

    modenum = -1
    for i in range(3):
     commands.doExecuteCommand("serialcommand,espnow,mode",False)
     time.sleep(0.5)
     scmdarr = getlastseriallogs(3)
     if len(scmdarr)>2:
      if ",mode" in scmdarr[2]:
       try:
        modenum = int(scmdarr[1])
        break
       except:
        modenum = -1
    if modenum!=-1: # valid number, process
     options = ["Gateway","Send only (remote config wont work!)","Receive only","Send&Receive"]
     optionvalues = [0,1,2,3]
     webserver.addFormSelector("Working mode","workmode",len(options),options,optionvalues,None,modenum)

     nodenum = -1
     commands.doExecuteCommand("serialcommand,unit",False)
     time.sleep(1)
     scmdarr = getlastseriallogs(3)
     if len(scmdarr)>2:
      if "unit" in scmdarr[2]:
       nodenum = scmdarr[1].replace("SERIAL: ","").strip()
       try:
        nodenum = int(nodenum)
       except:
        nodenum = -1
     if nodenum!=-1:
      webserver.addFormNumericBox("Unit number","nnodenum",nodenum,1,254)

     dnodenum = -1
     commands.doExecuteCommand("serialcommand,espnow,dest",False)
     time.sleep(1)
     scmdarr = getlastseriallogs(3)
     if len(scmdarr)>2:
      if ",dest" in scmdarr[2]:
       dnodenum = scmdarr[1].replace("SERIAL: ","").strip()
       try:
        dnodenum = int(dnodenum)
       except:
        dnodenum = -1
     webserver.addFormNumericBox("Destination node number","dnodenum",dnodenum,0,254)

     sdat = ""
     commands.doExecuteCommand("serialcommand,espnow,name",False)
     time.sleep(1)
     scmdarr = getlastseriallogs(3)
     if len(scmdarr)>2:
      if ",name" in scmdarr[2]:
       sdat = scmdarr[1].replace("SERIAL: ","").strip()
     webserver.addFormTextBox("Unit name","name",sdat,25)

     wchan = -1
     commands.doExecuteCommand("serialcommand,espnow,chan",False)
     time.sleep(1)
     scmdarr = getlastseriallogs(3)
     if len(scmdarr)>2:
      if ",chan" in scmdarr[2]:
       wchan = scmdarr[1].replace("SERIAL: ","").strip()
       try:
        wchan = int(wchan)
       except:
        wchan = -1
     if wchan!=-1:
      options = []
      optionvalues = []
      for i in range(1,14):
       options.append(str(i))
       optionvalues.append(i)
      webserver.addFormSelector("Wifi channel","wchannel",len(options),options,optionvalues,None,wchan)

     ds = -1
     commands.doExecuteCommand("serialcommand,espnow,deepsleep",False)
     time.sleep(1)
     scmdarr = getlastseriallogs(3)
     if len(scmdarr)>2:
      if ",deep" in scmdarr[2]:
       ds = scmdarr[1].replace("SERIAL: ","").strip()
       try:
        ds = int(ds)
       except:
        ds = -1
     if ds != -1:
      webserver.addFormNumericBox("DeepSleep timeout","deepsleep",ds,0,4294)
      webserver.addUnit("s")
      webserver.addFormNote("0 means disabled state,1-4294 means deep sleep timout in sec")
     webserver.addHtml("<input type='hidden' name='nodenum' value='"+str(managenode)+"'>")
     webserver.addSubmitButton("Save settings", "savelocal")
     webserver.addButton("espnow","Back")
     webserver.TXBuffer += "</form>"
#    print(scmdarr,modenum)
   elif str(managenode)!="": # display remote settings page
    webserver.addFormHeader("Node management")
#    commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,name",False)
    webserver.TXBuffer += "<form name='manespnow' method='post'><table class='multirow'>"

    modenum = -1
    for i in range(3):
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,mode",False)
     time.sleep(1)
     scmdarr = getlastespnowlogs(1)
     if len(scmdarr)>0:
       try:
        modenum = int(scmdarr[0])
        break
       except:
        modenum = -1
    if modenum!=-1: # valid number, process
     options = ["Gateway","Send only (remote config wont work!)","Receive only","Send&Receive"]
     optionvalues = [0,1,2,3]
     webserver.addFormSelector("Working mode","workmode",len(options),options,optionvalues,None,modenum)

     nodenum = -1
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",unit",False)
     time.sleep(2)
     scmdarr = getlastespnowlogs(1)
     if len(scmdarr)>0:
       try:
        nodenum = int(scmdarr[0])
       except:
        nodenum = -1
     webserver.addFormNumericBox("Unit number","nnodenum",nodenum,1,254)

     dnodenum = -1
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,dest",False)
     time.sleep(2)
     scmdarr = getlastespnowlogs(1)
     if len(scmdarr)>0:
       try:
        dnodenum = int(scmdarr[0])
       except:
        dnodenum = -1
     webserver.addFormNumericBox("Destination node number","dnodenum",dnodenum,0,254)
     webserver.addFormNote("If destination is not the same as your UNIT number ("+str(Settings.Settings["Unit"])+") you will NOT get any data from this remote!!!")

     sdat = ""
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,name",False)
     time.sleep(3)
     scmdarr = getlastespnowlogs(1)
     if len(scmdarr)>0:
       sdat = scmdarr[0]
     webserver.addFormTextBox("Unit name","name",sdat,25)

     wchan = -1
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,chan",False)
     time.sleep(2)
     scmdarr = getlastespnowlogs(1)
     if len(scmdarr)>0:
       try:
        wchan = int(scmdarr[0])
       except:
        wchan = -1
     options = []
     optionvalues = []
     for i in range(1,14):
      options.append(str(i))
      optionvalues.append(i)
     webserver.addFormSelector("Wifi channel","wchannel",len(options),options,optionvalues,None,wchan)

     ds = 0
     commands.doExecuteCommand("espnowcommand,"+str(managenode)+",espnow,deepsleep",False)
     time.sleep(2)
     scmdarr = getlastespnowlogs(1)
     if len(scmdarr)>0:
       try:
        ds = int(scmdarr[0])
       except:
        ds = 0
     webserver.addFormNumericBox("DeepSleep timeout","deepsleep",ds,0,4294)
     webserver.addUnit("s")
     webserver.addFormNote("0 means disabled state,1-4294 means deep sleep timout in sec")
     webserver.addHtml("<input type='hidden' name='nodenum' value='"+str(managenode)+"'>")
     webserver.addSubmitButton("Save settings", "savenode")
     webserver.addButton("espnow","Back")
     webserver.TXBuffer += "</form>"
#    print(str(managenode))
   webserver.sendHeadandTail("TmplStd",webserver._TAIL)
   return webserver.TXBuffer
  except Exception as e:
    print(e)
  return ""

pluginparams = [
{"pluginid":1,
"name":"Switch input",
"pins":1,
"ports":0,
"pullup":1,
"inverse":1,
"conf": 
 [
  {"name":"Type","type":"select","options":["Switch","Dimmer"],"optionvalues":[1,2]},
  {"name":"Dim","type":"num"},
  {"name":"Button type","type":"select","options":["Normal","Push Active Low","Push Active High"],"optionvalues":[0,1,2]},
  {"name":"Send boot state","type":"bool"}
 ]
},
{"pluginid":2,
"name":"Analog input",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":3,
"name":"Pulse Counter",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Debounce time","type":"num"},
  {"name":"Type","type":"select","options":["Delta","Delta/Total/Time","Total"],"optionvalues":[0,1,2]},
 ]
},
{"pluginid":5,
"name":"DHT",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Type","type":"select","options":["DHT11","DHT22","DHT12"],"optionvalues":[11,22,12]},
 ]
},
{"pluginid":6,
"name":"BMP085",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Altitude","type":"num"},
 ]
},
{"pluginid":7,
"name":"PCF8591",
"pins":0,
"ports":4, # Settings.TaskDevicePort
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":8,
"name":"RFID",
"pins":2,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":9,
"name":"MCP23017",
"pins":0,
"ports":16,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Send boot state","type":"bool"}
 ]
},
{"pluginid":10,
"name":"BH1750",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"I2C address","type":"select","options":["0x23","0x5c"],"optionvalues":[0x23,0x5c]},
 ]
},
{"pluginid":11,
"name":"ProMini Ext",
"pins":0,
"ports":14,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Type","type":"select","options":["Digital","Analog"],"optionvalues":[0,1]},
 ]
},
{"pluginid":13,
"name":"HC-SR04",
"pins":2,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Mode","type":"select","options":["Value","State"],"optionvalues":[1,2]},
  {"name":"Threshold","type":"num"},
 ]
},
{"pluginid":15,
"name":"Si7021",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":10,
"name":"TLS2561",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Integration time","type":"select","options":["13 ms","101 ms","402 ms"],"optionvalues":[0,1,2]},
 ]
},
{"pluginid":16,
"name":"IR receive",
"pins":1,
"ports":0,
"pullup":1,
"inverse":1,
"conf": []
},
{"pluginid":17,
"name":"PN532",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":18,
"name":"Sharp GP2Y10",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":19,
"name":"PCF8574",
"pins":0,
"ports":8, # Settings.TaskDevicePort
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Send boot state","type":"bool"}
 ]
},
{"pluginid":22,
"name":"PCA9685",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf":[]
},
{"pluginid":24,
"name":"MLX90614",
"pins":0,
"ports":16,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Option","type":"select","options":["IR object temp","Ambient temp"],"optionvalues":[7,6]},
 ]
},
{"pluginid":25,
"name":"ADS1115",
"pins":0,
"ports":4,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Gain","type":"select","options":["2/3x","1x","2x","4x","8x","16x"],"optionvalues":[0,2,4,6,8,10]},
 ]
},
{"pluginid":26,
"name":"SysInfo",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Indicator","type":"select","options":["Uptime","Free RAM","Wifi RSSI","Input VCC","System load"],"optionvalues":[0,1,2,3,4]},
 ]
},
{"pluginid":27,
"name":"INA219",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"Report","type":"select","options":["Voltage","Current","Power"],"optionvalues":[0,1,2]},
 ]
},
{"pluginid":28,
"name":"BME280",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"I2C address","type":"select","options":["0x76","0x77"],"optionvalues":[0x76,0x77]},
  {"name":"Altitude","type":"num"},
 ]
},
{"pluginid":30,
"name":"BMP280",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": 
 [
  {"name":"I2C address","type":"select","options":["0x76","0x77"],"optionvalues":[0x76,0x77]},
  {"name":"Altitude","type":"num"},
 ]
},
{"pluginid":31,
"name":"SHT1X",
"pins":2,
"ports":0,
"pullup":1,
"inverse":0,
"conf": []
},
{"pluginid":32,
"name":"MS5611",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": [
  {"name":"I2C address","type":"select","options":["0x77","0x76"],"optionvalues":[0x77,0x76]},
  {"name":"Altitude","type":"num"},
 ]
},
{"pluginid":33,
"name":"Dummy",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": [
  {"name":"I2C address","type":"select","options":["Single","Hum","Baro","Hum+Baro","Dual","Triple","Quad","Switch","Dimmer"],
   "optionvalues":[rpieGlobals.SENSOR_TYPE_SINGLE, rpieGlobals.SENSOR_TYPE_TEMP_HUM,rpieGlobals.SENSOR_TYPE_TEMP_BARO,rpieGlobals.SENSOR_TYPE_TEMP_HUM_BARO,rpieGlobals.SENSOR_TYPE_DUAL,rpieGlobals.SENSOR_TYPE_TRIPLE,rpieGlobals.SENSOR_TYPE_QUAD,rpieGlobals.SENSOR_TYPE_SWITCH,rpieGlobals.SENSOR_TYPE_DIMMER]},
  {"name":"Altitude","type":"num"},
 ]
},
{"pluginid":34,
"name":"DHT12",
"pins":0,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":35,
"name":"IRTX",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": []
},
{"pluginid":38,
"name":"Neopixel",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": [
  {"name":"LED Count","type":"num"},
]
},
{"pluginid":41,
"name":"NeoClock",
"pins":1,
"ports":0,
"pullup":0,
"inverse":0,
"conf": [
  {"name":"Red","type":"num"},
  {"name":"Green","type":"num"},
  {"name":"Blue","type":"num"},
]
},
]

def displaytask(taskstr,confstr):
  global pluginparams
  if type(taskstr)==list:
   ts = taskstr
   cs = confstr
  else:
   ts = str(taskstr).split(",")
   cs = str(confstr).split(",")
  pp = -1
  for p in range(len(pluginparams)):
   if int(pluginparams[p]["pluginid"])==int(ts[2]):
    pp = p
    break
  options = []
  optionvalues = []
  for p in range(len(pluginparams)):
    options.append(pluginparams[p]["name"])
    optionvalues.append(pluginparams[p]["pluginid"])
  webserver.addFormSelector("Plugin","pluginid",len(options),options,optionvalues,None,int(ts[2]))
  webserver.addFormNumericBox("Interval","interval",int(ts[7]),0,32768)
  webserver.addFormNumericBox("IDX","idx",int(ts[8]),0,32768)
  if pp>-1:
   try:
    options = []
    optionvalues = []
    for p in range(17):
     options.append("GPIO"+str(p))
     optionvalues.append(p)
    for i in range(0,pluginparams[pp]["pins"]):
     webserver.addFormSelector("Pin"+str(i+1),"pin"+str(i+1),len(options),options,optionvalues,None,int(ts[3+i]))
   except:
    pass
   try:
    if pluginparams[pp]["ports"]>0:
     webserver.addFormNumericBox("Port","port",int(ts[6]),0,32768)
   except:
    pass
   try:
    if pluginparams[pp]["pullup"]>0:
     webserver.addFormCheckBox("Internal pullup","pullup",int(cs[2])==1)
   except:
    pass
   try:
    if pluginparams[pp]["inverse"]>0:
     webserver.addFormCheckBox("Inversed logic","inverse",int(cs[3])==1)
   except:
    pass
   try:
    if len(pluginparams[pp]["conf"])>0:
     for i in range(len(pluginparams[pp]["conf"])):
      typedef = pluginparams[pp]["conf"][i]
      if typedef["type"]=="select":
       webserver.addFormSelector(typedef["name"],"c"+str(i),len(typedef["options"]),typedef["options"],typedef["optionvalues"],None,int(cs[4+i]))
      elif typedef["type"]=="bool":
       webserver.addFormCheckBox(typedef["name"],"c"+str(i),int(cs[4+i])==1)
      elif typedef["type"]=="num":
       webserver.addFormNumericBox(typedef["name"],"c"+str(i),int(cs[4+i]),0,32768)
   except Exception as e:
    print(e)
