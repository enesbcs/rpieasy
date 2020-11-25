#!/usr/bin/env python3
#############################################################################
################## RC522 RFID Reader for RPIEasy ############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import gpios
from mfrc522 import MFRC522

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 211
 PLUGIN_NAME = "RFID - RC522"
 PLUGIN_VALUENAME1 = "Tag"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SPI
  self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = False
  self.timeroptional = False
  self.formulaoption = False
  self.reader = None
  self.lastread = 0
  self.readinprogress = 0
  self.trigger = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = -1
  self.initialized = False
  if self.enabled:
   try:
     spil = self.spi
   except:
     spil = -1
   try:
    rstpin = self.taskdevicepin[0]
   except:
    rstpin = -1
    spil = -1
   try:
    ipin = self.taskdevicepin[1]
   except:
    ipin = -1
    spil = -1
   if spil>-1:
    try:
     gpios.HWPorts.remove_event_detect(int(ipin))
    except:
     pass
    try:
     self.reader = MFRC522(bus=spil,device=self.spidnum,pin_rst=rstpin)
     self.initialized = True
     self.timer100ms = True
     self.readinprogress = 0
     self.trigger = 0
     self.lastread = 0
     try:
      if ipin>-1:
       gpios.HWPorts.add_event_detect(int(ipin),gpios.FALLING,self.callback)
     except:
      pass
     self.rc_clear_irq()
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"RC522 init ok")
    except Exception as e:
     self.initialized = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RC522 init error:"+str(e))
  if self.initialized==False:
     self.timer100ms = False

 def timer_ten_per_second(self):
     if self.timer100ms and self.initialized and self.trigger==0 and self.readinprogress==0:
      self.trigger=1
      try:
       self.rc_activate_trigger()
      except:
       pass
      self.trigger=0
     return self.timer100ms

 def callback(self,channel):
    if self.readinprogress==0:
      self.readinprogress = 1
      if time.time()-self.lastread>=2: #do not retrigger within 2 seconds
       id = None
       try:
        c = 0
        while not id and c<3:
          id = self.rc_read_id_no_block()
          c += 1
       except Exception as e:
        id = None
       if id is not None:
        self.set_value(1,str(id),True)
        self.lastread = time.time()
        self._lastdataservetime = rpieTime.millis()
      else:
       time.sleep(0.5) #suppress quick readings
      self.readinprogress = 0
    self.rc_clear_irq()
    if self.trigger==0:
      self.rc_activate_trigger()

 def rc_uid_to_num(self,uid):
      n = 0
      for i in range(0, 5):
          n = n * 256 + uid[i]
      return n

 def rc_read_id_no_block(self):
      (status, TagType) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
      if status != self.reader.MI_OK:
          return None
      (status, uid) = self.reader.MFRC522_Anticoll()
      if status != self.reader.MI_OK:
          return None
      return self.rc_uid_to_num(uid)

 def rc_activate_trigger(self):
      self.reader.Write_MFRC522(0x09,0x26)
      self.reader.Write_MFRC522(0x01,0x0C)
      self.reader.Write_MFRC522(0x0D,0x87)

 def rc_clear_irq(self):
      self.reader.Write_MFRC522(0x04,0x7F) # clear all active irq
      self.reader.Write_MFRC522(0x02,0xA0) # ComIEnReg active low, receive int

 def webform_load(self): # create html page for settings
  webserver.addFormPinSelect("Reset pin (required)","taskdevicepin1",self.taskdevicepin[0])
  webserver.addFormNote("Set to an Output pin connected to RC522 reset pin!")
  webserver.addFormPinSelect("IRQ pin (required)","taskdevicepin2",self.taskdevicepin[1])
  webserver.addFormNote("Set to an Input-Pullup pin connected to RC522 IRQ pin!")
  return True

 def webform_save(self,params): # process settings post reply
   changed = False
   par = webserver.arg("taskdevicepin1",params)
   if par == "":
    par = 25
   pval = self.taskdevicepin[0]
   self.taskdevicepin[0] = int(par)
   if pval != self.taskdevicepin[0]:
    changed = True
   par = webserver.arg("taskdevicepin2",params)
   if par == "":
    par = 18
   pval = self.taskdevicepin[1]
   self.taskdevicepin[1] = int(par)
   if pval != self.taskdevicepin[1]:
    changed = True
   if changed:
    self.plugin_init()
   return True

 def plugin_exit(self):
  self.initialized = False
  self.timer100ms = False
  return True
