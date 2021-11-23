#!/usr/bin/env python3
#############################################################################
################## ESPEasy P2P controller for RPIEasy #######################
#############################################################################
#
# This controller is able to join ESPEasy P2P network, with auto registering
# itself, watching for Node advertisements, importing and exporting sensor
# data and information, and supports standard "sendto,unit" command scheme.
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import misc
import rpieGlobals
import time
import webserver
import commands
import Settings
import socket
import struct
import threading
try:
 import os_os as OS
except:
 print("OS function import error")

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 13
 CONTROLLER_NAME = "ESPEasy P2P"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.onmsgcallbacksupported = False # use direct set_value() instead of generic callback to make sure that values setted anyway
  self.controllerport = 65501
  self.timer30s = True
  self.bgproc = None
  self.netmethod = 0
  self.ownip = ""
  self.ownmac = ""

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  if self.enabled:
   self.bgproc = threading.Thread(target=self.bgreceiver)
   self.bgproc.daemon = True
   self.bgproc.start()
#   self.timer_thirty_second()
  try:
   nm = self.netmethod
  except:
   self.netmethod = 0
   self.ownip = ""
  self.initialized = True
  return True

 def webform_load(self):
  webserver.addFormNote("Hint: only the Controller Port parameter used!")
  options = ["Primary net","Secondary net","Manual"]
  optionvalues = [0,1,2]
  try:
   netm = self.netmethod
  except:
   netm = 0
  webserver.addFormSelector("IP address","c013_net",len(optionvalues),options,optionvalues,None,int(netm))
  try:
   oip = self.ownip
  except:
   oip = ""
  if netm != 2:
   oip = ""
  elif oip == "":
   oip = str(OS.get_ip())
  webserver.addFormTextBox("Force own IP to broadcast","c013_ip",str(oip),16)
  return True

 def webform_save(self,params):
     self.netmethod = int(webserver.arg("c013_net",params))
     if self.netmethod == 2:
      self.ownip = str(webserver.arg("c013_ip",params))
     else:
      self.ownip = ""

 def nodesort(self,item):
  v = 0
  try:
   v = int(item["unitno"])
  except:
   v = 0
  return v

 def bgreceiver(self): # start with threading!
  if self.enabled:
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Make Socket Reusable
   s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Allow incoming broadcasts
   s.setblocking(False) # Set socket to non-blocking mode
   s.bind(('',int(self.controllerport)))
#   data =''
   address = ''
   dp = data_packet()
   while self.enabled:
    dp.clear()
    try:
        dp.buffer,address = s.recvfrom(10000)
    except socket.error:
        pass
    else:
        try:
         dp.decode()
        except Exception as e:
         dp.pkgtype=0
        if dp.pkgtype==1:
         un = getunitordfromnum(dp.infopacket["unitno"]) # process incoming alive reports
         if un==-1:
          Settings.nodelist.append({"unitno":dp.infopacket["unitno"],"name":dp.infopacket["name"],"build":dp.infopacket["build"],"type":dp.infopacket["type"],"ip":dp.infopacket["ip"],"port":dp.infopacket["port"],"age":0})
          misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"New P2P unit discovered: "+str(dp.infopacket["unitno"])+" "+str(dp.infopacket["ip"])+" "+str(dp.infopacket["mac"]))
          Settings.nodelist.sort(reverse=False,key=self.nodesort)
         else:
          Settings.nodelist[un]["age"] = 0
          Settings.nodelist[un]["ip"] = dp.infopacket["ip"]
          Settings.nodelist[un]["port"] = dp.infopacket["port"]
          Settings.nodelist[un]["name"] = dp.infopacket["name"]
          if int(dp.infopacket["unitno"]) != int(Settings.Settings["Unit"]):
           misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Unit alive: "+str(dp.infopacket["unitno"]))
        elif dp.pkgtype==3:                              # process incoming new devices
          if int(Settings.Settings["Unit"])==int(dp.sensorinfo["dunit"]): # process only if we are the destination
           rtaskindex = int(dp.sensorinfo["dti"])
           if len(Settings.Tasks)<=rtaskindex or Settings.Tasks[rtaskindex]==False: # continue only if taskindex is empty
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sensorinfo arrived from unit "+str(dp.sensorinfo["sunit"]))
            devtype = 33
            for x in range(len(rpieGlobals.deviceselector)):
             if int(rpieGlobals.deviceselector[x][1]) == int(dp.sensorinfo["dnum"]):
              devtype = int(dp.sensorinfo["dnum"])
              break
            m = False
            try:
             for y in range(len(rpieGlobals.deviceselector)):
              if int(rpieGlobals.deviceselector[y][1]) == devtype:
               if len(Settings.Tasks)<=rtaskindex:
                while len(Settings.Tasks)<=rtaskindex:
                 Settings.Tasks.append(False)
               m = __import__(rpieGlobals.deviceselector[y][0])
               break
            except:
             m = False
            if m:
             try:
              Settings.Tasks[rtaskindex] = m.Plugin(rtaskindex)
             except:
              Settings.Tasks.append(m.Plugin(rtaskindex))
             Settings.Tasks[rtaskindex].plugin_init(False)
             Settings.Tasks[rtaskindex].remotefeed = True  # Mark that this task accepts incoming data updates!
             Settings.Tasks[rtaskindex].taskname = dp.sensorinfo["taskname"]
             for v in range(4):
              dp.sensorinfo["valuenames"].append("")
             for v in range(Settings.Tasks[rtaskindex].valuecount):
               Settings.Tasks[rtaskindex].valuenames[v] = dp.sensorinfo["valuenames"][v]
        elif dp.pkgtype==5:                          # process incoming data
          if int(Settings.Settings["Unit"])==int(dp.sensordata["dunit"]): # process only if we are the destination
           rtaskindex = int(dp.sensordata["dti"])
           if len(Settings.Tasks)>rtaskindex and Settings.Tasks[rtaskindex] and Settings.Tasks[rtaskindex].remotefeed: # continue only if taskindex exists and accepts incoming datas
            misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Sensordata update arrived from unit "+str(dp.sensordata["sunit"]))
            for v in range(Settings.Tasks[rtaskindex].valuecount):
             Settings.Tasks[rtaskindex].set_value(v+1,dp.sensordata["values"][v],False)
            Settings.Tasks[rtaskindex].plugin_senddata()

        elif dp.pkgtype==0:
          misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Command arrived from "+str(address))
          try:
           cmdline = decodezerostr(dp.buffer)
          except:
           cmdline = ""
          if len(cmdline)>1:
           commands.doExecuteCommand(cmdline,True)
    time.sleep(0.01) # sleep to avoid 100% cpu usage

 def udpsender(self,unitno,data,retrynum=1):
  destip = ""
  if unitno==255:
   destip = "255.255.255.255"
  else:
   for n in Settings.nodelist:
    if n["unitno"] == unitno:
     destip = n["ip"]
     break
  if destip != "":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if unitno==255:
     s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if type(data) is bytes:
     dsend = data
    elif type(data) is str:
     dsend = bytes(data,"utf-8")
    else:
     dsend = bytes(data)
    for r in range(retrynum):
      try:
#       print(dsend," ",destip," ",self.controllerport) # DEBUG
       s.sendto(dsend, (destip,int(self.controllerport)))
      except:
       pass
      if r<retrynum-1:
       time.sleep(0.1)

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if tasknum is None:
   return False
  if tasknum!=-1 and self.enabled:
   if tasknum<len(Settings.Tasks):
    if Settings.Tasks[tasknum] != False:
     if Settings.Tasks[tasknum].feedpublished == False:
      dp2 = data_packet() # publish sensor info if not yet published
      dp2.sensorinfo["sunit"] = Settings.Settings["Unit"]
      dp2.sensorinfo["sti"] = tasknum
      dp2.sensorinfo["dti"] = tasknum
      dp2.sensorinfo["dnum"] = Settings.Tasks[tasknum].getpluginid()
      dp2.sensorinfo["taskname"] = Settings.Tasks[tasknum].gettaskname()
      for u in range(Settings.Tasks[tasknum].valuecount):
       dp2.sensorinfo["valuenames"][u] = Settings.Tasks[tasknum].valuenames[u]
      procarr = []
      for n in Settings.nodelist: # send to all known nodes
        if int(n["unitno"]) != int(Settings.Settings["Unit"]):
         dp2.sensorinfo["dunit"] = n["unitno"]
         dp2.encode(3)
#         self.udpsender(n["unitno"],dp2.buffer,2)
         t = threading.Thread(target=self.udpsender, args=(n["unitno"],dp2.buffer,2))
         t.daemon = True
         procarr.append(t)
         t.start()
      if len(procarr)>0:
       for process in procarr:
        process.join()
      Settings.Tasks[tasknum].feedpublished = True # mark as published

     dp2 = data_packet() # do actual data sending
     dp2.sensordata["sunit"] = Settings.Settings["Unit"]
     dp2.sensordata["sti"] = tasknum
     dp2.sensordata["dti"] = tasknum
     for u in range(Settings.Tasks[tasknum].valuecount):
      dp2.sensordata["values"][u] = Settings.Tasks[tasknum].uservar[u]
     procarr = []
     for n in Settings.nodelist: # send to all known nodes
        if int(n["unitno"]) != int(Settings.Settings["Unit"]):
         dp2.sensordata["dunit"] = n["unitno"]
         dp2.encode(5)
#         self.udpsender(n["unitno"],dp2.buffer,2)
         t = threading.Thread(target=self.udpsender, args=(n["unitno"],dp2.buffer,2))
         t.daemon = True
         procarr.append(t)
         t.start()
     if len(procarr)>0:
       for process in procarr:
        process.join()

 def timer_thirty_second(self):
  if self.enabled:
  #send alive signals
   dp = data_packet()
   dp.infopacket["mac"] = "00:00:00:00:00:00"
   dp.infopacket["ip"] = ""
   if self.netmethod == 2:
    try:
     defdev = Settings.NetMan.getprimarydevice()
    except Exception as e:
     defdev = -1
    if defdev != -1:
     try:
      dp.infopacket["mac"] = Settings.NetworkDevices[defdev].mac
     except:
      pass
    else:
     try:
      defdev = Settings.NetMan.getsecondarydevice()
     except Exception as e:
      defdev = -1
     if defdev != -1:
      try:
       dp.infopacket["mac"] = Settings.NetworkDevices[defdev].mac
      except:
       pass
    dp.infopacket["ip"] = self.ownip
   elif self.netmethod == 0:
    try:
     defdev = Settings.NetMan.getprimarydevice()
    except Exception as e:
     defdev = -1
    if defdev != -1:
     try:
      dp.infopacket["mac"] = Settings.NetworkDevices[defdev].mac
      dp.infopacket["ip"] = Settings.NetworkDevices[defdev].ip
     except:
      pass
   elif self.netmethod == 1:
    try:
     defdev = Settings.NetMan.getsecondarydevice()
    except Exception as e:
     defdev = -1
    if defdev != -1:
     try:
      dp.infopacket["mac"] = Settings.NetworkDevices[defdev].mac
      dp.infopacket["ip"] = Settings.NetworkDevices[defdev].ip
     except:
      pass
   if dp.infopacket["ip"] == "":
    try:
     dp.infopacket["ip"] = str(OS.get_ip())
    except:
     pass
   if dp.infopacket["ip"] == "":
     dp.infopacket["ip"] = "0.0.0.0"
   dp.infopacket["unitno"] = int(Settings.Settings["Unit"])
   dp.infopacket["build"] = int(rpieGlobals.BUILD)
   dp.infopacket["name"] = Settings.Settings["Name"]
   dp.infopacket["type"] = int(rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD)
   dp.infopacket["port"] = int(Settings.WebUIPort)
   try:
    dp.encode(1)
    self.udpsender(255,dp.buffer,1)
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"C013 sysinfo: "+str(e))
   #clear old nodes
   for n in range(len(Settings.nodelist)):
    try:
     if Settings.nodelist[n]["age"] >= 10:
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"P2P unit disappeared: "+str(Settings.nodelist[n]["unitno"]))
      del Settings.nodelist[n]
     else:
      Settings.nodelist[n]["age"] += 1
    except:
     pass
  return True

class data_packet:
 buffer = bytearray(255)
 infopacket = {"mac":"","ip":"","unitno":-1,"build":0,"name":"","type":0,"port":80}
 sensorinfo = {"sunit":0,"dunit":0,"sti":0,"dti":0,"dnum":0,"taskname":"","valuenames":["","","",""]}
 sensordata = {"sunit":0,"dunit":0,"sti":0,"dti":0,"values":[0,0,0,0]}
 pkgtype = 0

 def __init__(self):
  self.clear()

 def clear(self):
  self.buffer = bytearray(255)
  self.infopacket["mac"] = ""
  self.infopacket["ip"] = ""
  self.infopacket["unitno"] = -1
  self.infopacket["build"] = 0
  self.infopacket["name"] = ""
  self.infopacket["type"] = 0
  self.infopacket["port"] = 80
  self.sensorinfo["sunit"] = 0
  self.sensorinfo["dunit"] = 0
  self.sensordata["sunit"] = 0
  self.sensordata["dunit"] = 0
  self.pkgtype = 0

 def encode(self,ptype):
  self.pkgtype = ptype
  if ptype == 1:
   tbuf = [255,1]
   ta = self.infopacket["mac"].split(":")
   if len(ta)<6:
    for i in range(0,6-len(ta)):
     ta.insert(0,"0")
   for m in ta:
    try:
     tbuf.append(int(m,16))
    except:
     tbuf.append(0)
   ta = self.infopacket["ip"].split(".")
   if len(ta)<4:
    for i in range(0,4-len(ta)):
     ta.insert(0,"0")
   for m in ta:
    try:
     tbuf.append(int(m))
    except:
     tbuf.append(255)
   if int(self.infopacket["unitno"])<0:
    self.infopacket["unitno"] = 0
   tbuf.append(int(self.infopacket["unitno"]))
   tbuf.append(int(self.infopacket["build"]%256))
   tbuf.append(int(self.infopacket["build"]/256))
   nl = len(self.infopacket["name"])
   if nl>24:
    nl = 24
   for s in range(nl):
    tbuf.append(ord(self.infopacket["name"][s]))
   try:
    for p in range(s,24):
     tbuf.append(0)
   except:
    pass
   tbuf.append(int(self.infopacket["type"]))
   tbuf.append(int(self.infopacket["port"]%256))
   tbuf.append(int(self.infopacket["port"]/256))
   for b in range(len(tbuf),80):
    tbuf.append(0)
   try:
    self.buffer = bytes(tbuf)
   except:
    self.buffer = bytes()
  if ptype == 3:
   tbuf = [255,3]
   tbuf.append(int(self.sensorinfo["sunit"]))
   tbuf.append(int(self.sensorinfo["dunit"]))
   tbuf.append(int(self.sensorinfo["sti"]))
   tbuf.append(int(self.sensorinfo["dti"]))
   if self.sensorinfo["dnum"] > 255: # bytes can go 0-255
    self.sensorinfo["dnum"] = 33
   tbuf.append(int(self.sensorinfo["dnum"]))
   sl = len(self.sensorinfo["taskname"])
   if sl>25:
    sl = 25
   for s in range(sl):
    tbuf.append(ord(self.sensorinfo["taskname"][s]))
   for p in range(s,25):
    tbuf.append(0)
   for v in range(rpieGlobals.VARS_PER_TASK):
    sl = len(self.sensorinfo["valuenames"][v])
    if sl>25:
     sl = 25
    for s in range(sl):
     tbuf.append(ord(self.sensorinfo["valuenames"][v][s]))
    for p in range(s,25):
     tbuf.append(0)
   for b in range(len(tbuf),137):
    tbuf.append(0)
   self.buffer = bytes(tbuf)
  if ptype == 5:
   tbuf = [255,5]
   tbuf.append(int(self.sensordata["sunit"]))
   tbuf.append(int(self.sensordata["dunit"]))
   tbuf.append(int(self.sensordata["sti"]))
   tbuf.append(int(self.sensordata["dti"]))
   tbuf.append(0) # Do not know why this 2 bytes necessarry...
   tbuf.append(0)
   for v in range(rpieGlobals.VARS_PER_TASK):
    try:
     val = float(self.sensordata["values"][v])
     cvf = list(struct.pack("<f",val))# convert float to bytearray
    except:
     if type(self.sensordata["values"][v]) is str:
      cvf = self.sensordata["values"][v][0:4]   # strip string if needed
     else:
      cvf = list(self.sensordata["values"][v])  # do anything that we can..
    cl = len(cvf)
    if cl>4:
     cl = 4
    for c in range(cl):
     tbuf.append(cvf[c])
   self.buffer = bytes(tbuf)

 def decode(self):
  tbuffer = list(self.buffer)
  self.pkgtype = 0
  if len(tbuffer)<1:
   self.clear()
   return 0
  if tbuffer[0] == 255:
   if tbuffer[1] == 1: # sysinfo len=80
    self.pkgtype = 1
    if len(self.buffer)>=41:
     cdata = struct.unpack_from('<B B 6B 4B B H 25s B H',self.buffer)
    else:
     cdata = struct.unpack_from('<B B 6B 4B B',self.buffer)
    array_alpha = cdata[2:8]
    self.infopacket["mac"] = ':'.join('{:02x}'.format(x) for x in array_alpha).upper()
    array_alpha = cdata[8:12]
    self.infopacket["ip"] = '.'.join(str(int(x)) for x in array_alpha)
    self.infopacket["unitno"] = int(cdata[12])
    try:
     self.infopacket["build"] = int(cdata[13])
     self.infopacket["name"] = decodezerostr(cdata[14])
     self.infopacket["type"] = int(cdata[15])
     pport = int(cdata[16])
     if pport not in [80,8008,8080]:
      pport = 80
     self.infopacket["port"] = pport
    except:
     pass
    if self.infopacket['type'] not in [rpieGlobals.NODE_TYPE_ID_ESP_EASY_STD, rpieGlobals.NODE_TYPE_ID_RPI_EASY_STD, rpieGlobals.NODE_TYPE_ID_ESP_EASYM_STD, rpieGlobals.NODE_TYPE_ID_ESP_EASY32_STD, rpieGlobals.NODE_TYPE_ID_ARDUINO_EASY_STD, rpieGlobals.NODE_TYPE_ID_NANO_EASY_STD, rpieGlobals.NODE_TYPE_ID_ATMEGA_EASY_LORA]:
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"P2P invalid type: "+str(self.infopacket['type']))
     self.pkgtype = 0 #invalid type, invalid pkt
   elif tbuffer[1] == 3: #sensor info min len=137
    self.pkgtype = 3
    if len(self.buffer)>162:
     cdata = struct.unpack_from('<B B B B B B B 26s 26s 26s 26s 26s 26s',self.buffer)
    else:
     cdata = struct.unpack_from('<B B B B B B B 26s 26s 26s 26s 26s',self.buffer)
    self.sensorinfo["sunit"] = int(cdata[2])
    self.sensorinfo["dunit"] = int(cdata[3])
    self.sensorinfo["sti"]   = int(cdata[4])
    self.sensorinfo["dti"]   = int(cdata[5])
    self.sensorinfo["dnum"]  = int(cdata[6])
    self.sensorinfo["taskname"] = decodezerostr(cdata[7])
    self.sensorinfo["valuenames"] = []
    for v in range(rpieGlobals.VARS_PER_TASK):
     tvn = decodezerostr(cdata[8+v])
     if tvn != "":
      self.sensorinfo["valuenames"].append(tvn)
   elif tbuffer[1] == 5: #sensor info min len=22
    self.pkgtype = 5
    cdata = struct.unpack_from('<8B 4f',self.buffer)
    self.sensordata["sunit"] = int(cdata[2])
    self.sensordata["dunit"] = int(cdata[3])
    self.sensordata["sti"]   = int(cdata[4])
    self.sensordata["dti"]   = int(cdata[5])
    self.sensordata["values"] = []
    for f in range(rpieGlobals.VARS_PER_TASK):
     self.sensordata["values"].append(float(cdata[8+f]))

# Helper functions

def getunitordfromnum(unitno):
  for n in range(len(Settings.nodelist)):
   if int(Settings.nodelist[n]["unitno"]) == int(unitno):
    return n
  return -1

def decodezerostr(barr):
 result = ""
 for b in range(len(barr)):
  if barr[b] == 0:
   try:
    result = barr[:b].decode("utf-8")
   except:
    result = str(barr[:b])
   break
 if b>=len(barr)-1:
   try:
    result = barr.decode("utf-8")
   except:
    result = str(barr)
 return result.strip()

