#!/usr/bin/env python3
#############################################################################
##################### Zabbix controller for RPIEasy #########################
#############################################################################
#
# Zabbix controller
#
# Copyright (C) 2018-2024 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import misc
import rpieGlobals
import time
import webserver
import Settings
import socket
import struct
import json
import threading
import Settings

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 17
 CONTROLLER_NAME = "Zabbix"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.onmsgcallbacksupported = False # use direct set_value() instead of generic callback to make sure that values setted anyway
  self.controllerport = 10051

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.initialized = True
  return True

 def webform_load(self):
     webserver.addFormNote("Value names will be transmitted as 'taskname-valuename' to Zabbix server!")

 def sender(self,data):
   try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect( (self.controllerip,int(self.controllerport)) )
    s.send(data)
    #resp_header = s.recv(5)
    #if 'ZBXD' in str(resp_header):
    # resp_header = s.recv(8)
    # resp_header = resp_header[:4]
    # response_len = struct.unpack('i', resp_header)[0]
    # response_raw = s.recv(response_len)
    # print(response_raw)
    s.close()
   except Exception as e:
    print(e)

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1): # called by plugin
  if tasknum is None:
   return False
  if tasknum!=-1 and self.enabled:
   if tasknum<len(Settings.Tasks):
    if Settings.Tasks[tasknum] != False:
      reply = {}
      reply['request'] = 'sender data'
      reply['data'] = []
      hostname = Settings.Settings["Name"]
      for u in range(Settings.Tasks[tasknum].valuecount):
       treply = {}
       treply["host"] = hostname
       treply["key"] = str(Settings.Tasks[tasknum].taskname).strip() + "-" + str(Settings.Tasks[tasknum].valuenames[u]).strip()
       treply["value"] = str(Settings.Tasks[tasknum].uservar[u])
       reply["data"].append(treply)
      HEADER = bytes('ZBXD','utf-8') + b'\x01'
      dstr = bytes(json.dumps(reply),'utf-8')
      dlen = len(dstr)
      dheader = struct.pack('i', dlen) + b'\0\0\0\0'
      datablob = HEADER + dheader + dstr
      t = threading.Thread(target=self.sender, args=(datablob,))
      t.daemon = True
      t.start()
      return True
