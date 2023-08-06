#!/usr/bin/env python3
#############################################################################
################## PN532 RFID Reader  for RPIEasy ###########################
#############################################################################
#
# Powered by Waveshare PN532 NFC Hat control library:
#  https://github.com/soonuse/pn532-nfc-hat
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import threading
import time
import gpios
import lib.pn532.i2c as pn532

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 17
 PLUGIN_NAME = "RFID - PN532"
 PLUGIN_VALUENAME1 = "Tag"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = False
  self.timeroptional = False
  self.formulaoption = False
  self.pn = None
  self.ver = ""
  self.lastread = 0
  self.processing = False
  self.i2cport = -1
  self.preset = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = -1
  self.initialized = False
  time.sleep(1)
  if self.enabled:
   try:
     i2cl = self.i2c
   except:
     i2cl = -1
   try:
    i2cport = gpios.HWPorts.geti2clist()
    if i2cl==-1:
      i2cl = int(i2cport[0])
   except:
    i2cport = []
   if len(i2cport)>0 and i2cl>-1:
    self.preset = str(self.taskdevicepin[0]).strip()
    if self.preset == "" or self.preset=="-1":
     self.preset = None
    else:
     try:
      self.preset = int(reset)
     except:
      self.preset = None
    self.ver = ""
    try:
     self.pn = pn532.PN532_I2C(reset=self.preset,i2c_c=self.i2c)
     ic,ver,rev,supp=self.pn.get_firmware_version() # get fw version
     self.ver = str(ver)+"."+str(rev)
     self.pn.SAM_configuration() # set mifare type
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"PN532 v"+str(self.ver)+" initialized")
     self.initialized = True
    except Exception as e:
     self.initialized = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PN532 init error:"+str(e))
    self.processing = False
    if self.initialized:
     bgt = threading.Thread(target=self.bgreader)
     bgt.daemon = True
     bgt.start()

 def bgreader(self):
   while self.enabled:
    if self.initialized:
     try:
      uid = self.pn.read_passive_target(timeout=1)
      if uid is not None:
       self.callbackfunc(uid)
     except Exception as e:
      pass
    else:
     time.sleep(0.1)

 def callbackfunc(self,rfid):
  if self.processing==False:
   self.processing = True
   tn = time.time()
   if (tn-self.lastread)>1:
    self.lastread=tn
    try:
     sval = str(int.from_bytes(rfid,byteorder='big',signed=False))
    except:
     sval = ""
    if sval != "":
     self.set_value(1,sval,True)
   self.processing = False

 def webform_load(self): # create html page for settings
  webserver.addFormNote("I2C address is fixed 0x24! You can check it at <a href='i2cscanner'>i2cscan</a> page.")
  webserver.addFormPinSelect("Reset pin (optional)","taskdevicepin3",self.taskdevicepin[0])
  webserver.addFormNote("Set to an Output pin connected to PN532 reset pin or None!")
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("taskdevicepin3",params)
   if par == "":
    par = -1
   self.taskdevicepin[0] = int(par)
   return True

 def __del__(self):
   self.initialized=False

 def plugin_exit(self):
  self.__del__()
  return True

