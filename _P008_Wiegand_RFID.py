#!/usr/bin/env python3
#############################################################################
################ Wiegand Reader plugin for RPIEasy ##########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import wiegand_io
import threading
import time
import hashlib

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 8
 PLUGIN_NAME = "RFID - Wiegand"
 PLUGIN_VALUENAME1 = "Tag"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = False
  self.timeroptional = False
  self.formulaoption = False
  self.bgreader = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = -1
  if self.taskdevicepin[0]>=0 and self.taskdevicepin[1]>=0 and self.enabled:
   try:
    wiegand_io.initreader(int(self.taskdevicepin[0]),int(self.taskdevicepin[1]))
   except Exception as e:
    print("Wiegand IO ERROR:",e)
    self.initialized = False
   if self.initialized:
    self.bgreader = BackgroundThread(self.callbackfunc,0.005) # 0.005?
  else:
   self.initialized = False
   self.enabled = False
   if self.bgreader is not None:
    self.bgreader.stoprun()

 def __del__(self):
   if self.bgreader is not None:
    self.bgreader.stoprun()

 def plugin_exit(self):
  self.__del__()
  return True

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = ["RAW","SHA1 encoded","SHA1 encoded except starting with 0"]
  optionvalues = [0,1,2]
  webserver.addFormSelector("Sending format","p008_format",3,options,optionvalues,None,choice1)
  return True

 def webform_save(self,params):
  par = webserver.arg("p008_format",params)
  if par == "":
   par = 0
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def callbackfunc(self,ctype,rfid): # this function is called by wiegand io if RFID card showed or PIN entered
#  print(ctype,rfid) # DEBUG
  sval = ""
  if len(str(rfid))>0:
   if ctype == 1:
    sval = str(rfid)
   elif ctype>1:
    if self.taskdevicepluginconfig[0]==0: # RAW
     sval = str(rfid)
    elif self.taskdevicepluginconfig[0]==2: # SHA1ex0
     if (str(rfid)[0] == '0') and (len(rfid)<20): # exclude commands (entered to keypad) that identified by starting zero
      sval = str(rfid)
     else:
      sval = hashlib.sha1(bytes(rfid,'utf-8')).hexdigest()
      if sval[0] == '0':
       sval[0] = '1' # dirty hack to remove zero from the start
    elif self.taskdevicepluginconfig[0]==1: # SHA1
     sval = hashlib.sha1(bytes(rfid,'utf-8')).hexdigest()
  if sval != "":
#   print(sval) # DEBUG
   self.set_value(1,sval,True)

 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "rfidclear":
   try:
    rname = cmdarr[1].strip()
   except:
    rname = ""
   if rname != "" and rname.lower() == self.gettaskname().lower():
    self.uservar[0] = "0"
    if self.bgreader is not None:
     try:
      self.bgreader.clearbuffer()
     except:
      pass
    res = True
  return res

class BackgroundThread(object):
   KEYPAD_ESC = 10
   KEYPAD_ENT = 11

   def __init__(self,callbackaddr,interval=0.005):
    self.interval = interval
    self.pin = ""
    self.enablerun = True
    self.callbackfunc = callbackaddr
    thread = threading.Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

   def analyzekey(self,keycode):
        key = int(keycode,2)
#       print("K:",key)
        if (key>=0) and (key<10):
         self.pin = ''.join([self.pin,chr(48+key)])
        elif key == self.KEYPAD_ESC:
         if len(self.pin)>0:
            self.pin = ""      # if PIN entered, delete from buffer
         else:
            self.callbackfunc(1,'ESC') # if no PIN in buffer, send ESC key
        elif key == self.KEYPAD_ENT:
         if len(self.pin)>0:
            self.callbackfunc(2,str(self.pin)) # if PIN buffer not empty, send PIN
            self.pin = ""                      # then clear buffer
         else:
            self.callbackfunc(1,'ENT') # if PIN buffer emtpy, send ENT key

   def run(self):
    while (self.enablerun):
     if (wiegand_io.pendingbitcount() > 0):
      wstr,wbl = wiegand_io.wiegandread()
#      print("Python res:",wstr,wbl)
      if wbl>2 and wbl<5:
       self.analyzekey(wstr)
      elif wbl>6 and wbl<9:
       self.analyzekey(wstr[:4])
       self.analyzekey(wstr[4:8])
      elif wbl > 20:
       self.callbackfunc(3,str(self.binaryToInt(wstr,wbl))) # send Card number as integer
     time.sleep(self.interval)

   def stoprun(self):
    self.enablerun = False

   def clearbuffer(self):
    self.pin = ""

   def binaryToInt(self,binary_string,blen):
                binary_string = binary_string[1:(blen-1)] #Removing the first and last bit (Non-data bits)
                try:
                    result = int(binary_string, 2)
                except:
                    result = 0
                return result
