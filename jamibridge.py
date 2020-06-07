#!/usr/bin/env python3
#############################################################################
################### Jami root user bridge for RPIEasy #######################
#############################################################################
#
# DBUS can be used only with the same user, this bridge forwards status through UDP
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import time
import socket
import threading
import lib.lib_dring as dring
import sys
import signal

class JamiBridge():

 def __init__(self):
     self.jami = None
     self.enabled = True
     self.rcontrollerport = 16080
     self.scontrollerport = 16081
     self.initialized = False
     self.uservar = [-1,-1,-1,-1]
     try:
      self.sessid = self.jami.sessid
     except:
      self.sessid = -1
     try:
       self.jami = dring.request_dring_channel("jamibridge",0,True) # create or get existing Jami handler from library
       self.jami.cb_call = self.cb_call
       self.jami.cb_text = self.cb_text
       self.jami.cb_ring2 = self.cb_ring2
       self.initialized = self.jami.initialized
     except Exception as e:
       print("JamiBrige init error: "+str(e))
     if self.initialized:
       if self.sessid != self.jami.sessid:
        signal.signal(signal.SIGINT, self.signal_handler)
        try:
         self.jami.daemon = True          # start it if not yet started
         self.jami.start()
        except:
         pass
       self.bgproc = threading.Thread(target=self.bgreceiver)
       self.bgproc.daemon = True
       self.bgproc.start()

 def signal_handler(self,signal,frame):
      self.initialized = False
      self.enabled = False
      time.sleep(0.1)
      sys.exit(0)
 
 def plugin_senddata(self,datapacket,cmdp="",types="0"):
     try:
      datapacket.encode(cmds=cmdp,typee=types)
      if len(datapacket.buffer)>0:
       self.udpsender(datapacket.buffer)    # send data through udp
     except Exception as e:
      print(e)

 def cb_ring2(self, stateid, statestr, caller=None):
     dp = dring.json_data_packet()
     if (int(self.uservar[0]) != stateid) and (stateid != 0):
      self.uservar[0]=stateid
      dp.set_value(1,stateid)
      dp.set_value(2,statestr)
      dp.set_value(3,caller)
      dp.set_value(4,"")
      self.plugin_senddata(dp,types="STAT")
     elif int(self.uservar[0]) in [1,2] and stateid==0:
      self.uservar[0]=0
      dp.set_value(1,0)
      dp.set_value(2,"INACTIVE")
      dp.set_value(4,"")
      self.plugin_senddata(dp,types="STAT")
     return True

 def cb_call(self, state):
#     print("call",state)#debug
     dp = dring.json_data_packet()
     if int(state)==1:
      self.uservar[0]=3
      dp.set_value(1,3)
      dp.set_value(2,"ACTIVE")
      dp.set_value(4,"")
      self.plugin_senddata(dp,types="STAT")
     elif int(self.uservar[0]) in [1,3]:
      self.uservar[0]=0
      dp.set_value(1,0)
      dp.set_value(2,"INACTIVE")
      dp.set_value(4,"")
      self.plugin_senddata(dp,types="STAT")
     return True

 def cb_text(self, fromacc, text):
#     print("text",fromacc,text)#debug
     try:
      dp = dring.json_data_packet()
      dp.set_value(1,10)
      dp.set_value(2,"MSG")
      dp.set_value(3,fromacc)
      dp.set_value(4,text)
      self.plugin_senddata(dp,types="MSG")
     except Exception as e: 
      print(e)
     return True

 def bgreceiver(self): # start with threading!
  if self.initialized:
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Make Socket Reusable
   s.setblocking(False) # Set socket to non-blocking mode
   s.bind(('',int(self.rcontrollerport)))
#   data =''
   address = ''
   dp = dring.json_data_packet()
   ds = dring.json_data_packet()
   while self.enabled:
    dp.clear()
    try:
        dp.buffer,address = s.recvfrom(10000)
    except socket.error:
        pass
    else:
      if dp.buffer[0]==123: # {
       dp.decode()
#       print("rec cmd ",dp.datapacket)#debug
       if "cmd" in dp.datapacket and "type" in dp.datapacket:
        if dp.datapacket["type"]=="CMD":
         ds.clear()
         if dp.datapacket["cmd"]=="call":
          try:
           self.jami.makeCall(dp.datapacket["val1"])
          except Exception as e:
           print(e)
#          print("call")
         elif dp.datapacket["cmd"]=="isoperational":
          ds.set_value(1,self.initialized)
          self.plugin_senddata(ds,types="RES",cmdp=dp.datapacket["cmd"])
#          print("isworking?",self.initialized)#debug
         elif dp.datapacket["cmd"]=="accept":
#          print("accept")
          self.jami.acceptIncoming()
         elif dp.datapacket["cmd"]=="refuse":
          self.jami.refuseIncoming()
         elif dp.datapacket["cmd"]=="endcall": # or refuse
          self.jami.endCall()
#          print("endcall")
         elif dp.datapacket["cmd"]=="getcontactlist":
          try:
           cl = self.jami.getContactList()
          except:
           cl = []
          ds.set_value(1,cl)
          self.plugin_senddata(ds,types="RES",cmdp=dp.datapacket["cmd"])
#          print("getcontactlist")
         elif dp.datapacket["cmd"]=="sendtext":
          try:
           self.jami.sendText(dp.datapacket["val1"],dp.datapacket["val2"])
          except Exception as e:
           print(e)
         elif dp.datapacket["cmd"]=="getstatus":
          ds.set_value(1,self.uservar[0])
          self.plugin_senddata(ds,types="RES",cmdp=dp.datapacket["cmd"])
#          print("getstatus")
         elif dp.datapacket["cmd"]=="getaccount":
          ds.set_value(1,self.jami.account)
          self.plugin_senddata(ds,types="RES",cmdp=dp.datapacket["cmd"])
#          print("getaccount")

    time.sleep(0.01) # sleep to avoid 100% cpu usage

 def udpsender(self,data):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if type(data) is bytes:
     dsend = data
    elif type(data) is str:
     dsend = bytes(data,"utf-8")
    else:
     dsend = bytes(data)
    try:
#       print(dsend," localhost ",self.scontrollerport) # DEBUG
       s.sendto(dsend, ("127.0.0.1",int(self.scontrollerport)))
    except Exception as e:
       print(e)

connok = False
print("Initialize connection with Jami DRingCtrl daemon...")
while connok==False: 
 try:
  JB = JamiBridge()
  connok = JB.initialized
 except:
  connok = False
 time.sleep(5)
print("Connection OK, starting loop. Data sending to localhost:"+str(JB.scontrollerport))
while JB.initialized:
 time.sleep(1)
# print(".")
