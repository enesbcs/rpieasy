#!/usr/bin/env python3
#############################################################################
################## DringCtrl helper library for RPIEasy #####################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
from gi.repository import GLib
from lib.dringctrl.errorsDring import DRingCtrlError
from lib.dringctrl.controller import DRingCtrl
import random
import time
import json
import threading
import socket
import hashlib

class JamiHandler(DRingCtrl):

    def __init__(self, name="",accountnum=0,a2way=False):
        super(JamiHandler, self).__init__(name, False)
        self.accountnum = accountnum
        self.jname = name
        self.initialized = False
        self.operational = False
        self.sessid = random.randrange(1,1000000)
        self.lastring = 0
        self.lastcall = 0
        self.last_msg = ""
        self.cb_ring  = None
        self.cb_call  = None
        self.cb_text  = None
        self.cb_ring2 = None
        self.uservar  = [-1,-1,-1,-1]
        try:
         ringAccounts = self.getAllAccounts('RING')
        except:
         ringAccounts = []
        if len(ringAccounts) > self.accountnum:
            self.initialized = True
            self.setAccount(ringAccounts[self.accountnum]) # use first address
        volatileCallerDetails = self.getVolatileAccountDetails(self.account)
        if volatileCallerDetails['Account.registrationStatus'] != 'REGISTERED':
            self.initialized = False
            raise DRingCtrlError("Caller Account not registered")
        print("Using local account: ", self.account, volatileCallerDetails['Account.registrationStatus'])
        self.operational = self.initialized

    def onIncomingCall_cb(self, callId):
       if time.time()-self.lastring > 2:
        if self.cb_ring is not None:
         self.cb_ring(1,callId)
#        else:
#         print("----------Ringing")
        if self.cb_ring2 is not None:
          caller = "UNKNOWN"
          incoming = False
          if callId:
           try:
            cdetails = self.getCallDetails(callId)
            caller = str(cdetails['PEER_NUMBER'])
           except:
            pass
           try:
            incoming = (str(cdetails['CALL_STATE']) == "INCOMING")
           except:
            pass
          if "@ring.dht" in caller:
           caller = caller.replace("@ring.dht","")
          if incoming:
           self.uservar[0] = 1
           strstat = "RINGIN"
          else:
           self.uservar[0] = 2
           strstat = "RINGOUT"
          self.cb_ring2(self.uservar[0],strstat,caller)
        self.lastring = time.time()

    def onCallCurrent_cb(self):
       if time.time()-self.lastcall > 2:
        if self.cb_call is not None:
         self.cb_call(1)
#        else:
#         print("----------Call accepted, ring end")
        if self.cb_ring is not None:
         self.cb_ring(0,None)
        if self.cb_ring2 is not None:
         self.cb_ring2(0,"INACTIVE")
        self.lastcall = time.time()

    def onCallOver_cb(self):
        if self.cb_call is not None:
         self.cb_call(0)
#        else:
#         print("----------Call ended")

    def onIncomingAccountMessage(self, accountId, messageId, fromAccount, payloads=None):
      if payloads is None: # changes in API???
       try:
        if 'text/plain' in fromAccount:
         payloads = fromAccount
         fromAccount = messageId
         nid = str(payloads)+str(fromAccount)
         messageId = hashlib.md5(nid.encode("utf-8")).hexdigest() # old api has no messageId
#         accountId = self.account
        else:
         return
       except:
        pass
#      print("ai",accountId,"mi",messageId,"fa",fromAccount)#debug
      try:
       if self.last_msg != messageId: # filter same messages
        self.last_msg = messageId
        if self.cb_text is not None:
         self.cb_text(fromAccount,payloads['text/plain'])
#        else: 
#         print(fromAccount, payloads['text/plain'])
      except Exception as e:
       print(e)

    def getContactList(self):
     contacts = []
     try:
      dcontacts = self.getContacts(self.account) # get contacts from Jami
      if dcontacts:
       for i in range(len(dcontacts)):
        if 'confirmed' in dcontacts[i]:
         if dcontacts[i]['confirmed']:
          contacts.append(str(dcontacts[i]['id'])) # returns only enabled and confirmed ones
     except Exception as e:
      print(e)
     return contacts

    def acceptIncoming(self):
      self.Accept(self.currentCallId)

    def refuseIncoming(self):
      self.Refuse(self.currentCallId)

    def makeCall(self,target):
      self.Call(str(target),self.account)

    def endCall(self):
      self.HangUp(self.currentCallId) # end current call

    def sendText(self, dest, text):
      self.sendTextMessage(self.account, dest, text)

    def getAccount(self):
      return self.account

class json_data_packet:
 buffer = bytearray()
 datapacket = {"id":"","cmd":"","type":"","val1":"","val2":"","val3":"","val4":""}

 def __init__(self):
  self.clear()

 def clear(self):
  self.buffer = bytearray()
  self.datapacket = {"id":"","cmd":"","type":"","val1":"","val2":"","val3":"","val4":""}

 def set_value(self,valnum,value):
  try:
   if valnum==1:
    self.datapacket['val1']=str(value)
   elif valnum==2:
    self.datapacket['val2']=str(value)
   elif valnum==3:
    self.datapacket['val3']=str(value)
   elif valnum==4:
    self.datapacket['val4']=str(value)
   self.uservar[valnum-1]=value
  except:
   pass

 def encode(self,cmds="0",typee="0"):
  try:
   self.datapacket["cmd"]=str(cmds)
   self.datapacket["type"]=str(typee)
   self.datapacket["id"]="JU"
   tdata = json.dumps(self.datapacket)
   self.buffer = bytes(tdata,"utf-8")
  except Exception as e:
   print(e)
   self.buffer = bytes()
 
 def decode(self):
  try:
   self.datapacket = json.loads(self.buffer.decode("utf-8"))
  except Exception as e:
   print(e)
   self.datapacket["id"] = "INV"
   self.datapacket["cmd"] = ""
   self.datapacket["type"] = ""

class JamiBridgeHandler():

 def __init__(self, name="",accountnum=0,a2way=False):
     self.jami = None
     self.name = name
     self.accountnum = -1
     self.enabled = True
     self.daemon = False
     self.rcontrollerport = 16081
     self.scontrollerport = 16080
     self.initialized = True
     self.operational = False
     self.cb_call  = None
     self.cb_text  = None
     self.cb_ring2 = None
     self.uservar = [-1,-1,-1,-1]
     self.contactlist = []
     self.account = 0
     self.status = 0
     self.sessid = random.randrange(1,1000000)
     self.bgproc = threading.Thread(target=self.bgreceiver)
     self.bgproc.daemon = True
     self.bgproc.start()
     time.sleep(1)
     self.operational = self.isWorking(True)
     if self.operational:
      self.getStatus()
      self.getAccount()

 def start(self):
     pass

 def sendcmd(self,datapacket,cmdp="",types="CMD"):
     try:
      datapacket.encode(cmds=cmdp,typee=types)
      if len(datapacket.buffer)>0:
       self.udpsender(datapacket.buffer)    # send data through udp
     except Exception as e:
      print(e)

 def bgreceiver(self): # start with threading!
  if self.initialized:
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Make Socket Reusable
   s.setblocking(False) # Set socket to non-blocking mode
   s.bind(('',int(self.rcontrollerport)))
#   data =''
   address = ''
   dp = json_data_packet()
   while self.enabled:
    dp.clear()
    try:
        dp.buffer,address = s.recvfrom(10000)
    except socket.error:
        pass
    else:
       dp.decode()
       if "type" in dp.datapacket:
        if dp.datapacket["type"]=="RES":
         if "cmd" in dp.datapacket:
          if dp.datapacket["cmd"]=="isoperational":
           self.operational=dp.datapacket["val1"]
          elif dp.datapacket["cmd"]=="getcontactlist":
           self.contactlist= eval(dp.datapacket["val1"])
          elif dp.datapacket["cmd"]=="getaccount":
           self.account=dp.datapacket["val1"]
          elif dp.datapacket["cmd"]=="getstatus":
           try:
            stat = int(dp.datapacket["val1"])
           except:
            stat = -1
           if stat!=-1:
            self.status = stat
#         print("receiving result ",dp.datapacket)
        elif dp.datapacket["type"]=="STAT":
         if int(dp.datapacket["val1"])==0:
          if self.uservar[0] in [1,2]:
           if self.cb_ring2 is not None:
            self.cb_ring2(0,"INACTIVE")
          else:
           if self.cb_call is not None:
            self.cb_call(0)
         elif int(dp.datapacket["val1"]) in [1,2]:
           if self.cb_ring2 is not None:
            self.cb_ring2(int(dp.datapacket["val1"]),dp.datapacket["val2"],dp.datapacket["val3"])
         elif int(dp.datapacket["val1"])==3:
           if self.cb_call is not None:
            self.cb_call(1)
         self.uservar[0]=int(dp.datapacket["val1"])
        elif dp.datapacket["type"]=="MSG":
           if self.cb_text is not None:
            self.cb_text(dp.datapacket["val3"],dp.datapacket["val4"])

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

 def isWorking(self,wait=False):
     dp = json_data_packet()
     self.sendcmd(dp,"isoperational")
     time.sleep(0.5)      # wait for reply!!!
     return self.operational

 def getContactList(self):
     dp = json_data_packet()
     self.sendcmd(dp,"getcontactlist")
     time.sleep(0.5)      # wait for reply!!!
     return self.contactlist

 def acceptIncoming(self):
     dp = json_data_packet()
     self.sendcmd(dp,"accept")

 def refuseIncoming(self):
     dp = json_data_packet()
     self.sendcmd(dp,"refuse")
 
 def makeCall(self,target):
     dp = json_data_packet()
     dp.set_value(1,target)
     self.sendcmd(dp,"call")

 def endCall(self):
     dp = json_data_packet()
     self.sendcmd(dp,"endcall")

 def getAccount(self):
     dp = json_data_packet()
     self.sendcmd(dp,"getaccount")
     time.sleep(0.5)      # wait for reply!!!
     return self.account

 def getStatus(self):
     dp = json_data_packet()
     self.sendcmd(dp,"getstatus")

 def checkBridge(self):
     return True

 def sendText(self, dest, text):
     dp = json_data_packet()
     dp.set_value(1,dest)
     dp.set_value(2,text)
     self.sendcmd(dp,"sendtext")

 def stopThread(self):
     self.operational = False
     self.initialized = False
     self.enabled = False

dring_chn = []

def request_dring_channel(rname="",raccountnum=0, r2way=False):
    for i in range(len(dring_chn)):
     if (dring_chn[i].accountnum == int(raccountnum)):
      try:
       ea = dring_chn[i].getAllEnabledAccounts()
       valid = True
      except:
       valid = False
      if valid:
       return dring_chn[i]
      else:
       del dring_chn[i]
    dring_chn.append(JamiHandler(name=rname,accountnum=raccountnum,a2way=r2way))
    return dring_chn[-1]

def request_dring_bridge(rname="jamibridge"):
    for i in range(len(dring_chn)):
     if (dring_chn[i].name == str(rname)):
      try:
       ea = dring_chn[i].checkBridge()
       valid = True
      except:
       valid = False
      if valid:
       return dring_chn[i]
      else:
       del dring_chn[i]
    dring_chn.append(JamiBridgeHandler(name=rname))
    return dring_chn[-1]

#print("dr",dring_chn)
