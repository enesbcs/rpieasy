#!/usr/bin/env python3
#############################################################################
############### Duppa I2C Rotary encoder plugin for RPIEasy #################
#############################################################################
#
# Duppa.net I2C Rotary Encoder Breakout
#
# Needs an I2C connection enabled and an INT GPIO connected to RPI
#
# Copyright (C) 2024 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import gpios
import Settings
import lib.lib_miniencrouter as miniencoder

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 219
 PLUGIN_NAME = "Input - Duppa I2C Rotary Encoder"
 PLUGIN_VALUENAME1 = "Counter"
 PLUGIN_VALUENAME2 = "Button"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  self.valuecount = 2
  self.ports = 0
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.timer100ms = False
  self.enc = None
  self.readinprogress = 0
  self.formulaoption = True
  self.initialized = False
  self.interruptval = -1

 def plugin_exit(self):
  if self.enabled:
   if self.timer100ms==False:
    try:
     gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
    except:
     pass
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.decimals[1]=0
  self.readinprogress = 0
  self.interruptval = -1
  self.timer100ms = False
  self.initialized = False
  if self.enabled:
   if int(self.taskdevicepin[0])>=0:
    try:
     gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.FALLING,self.p219_handler)
    except Exception as e:
     self.timer100ms = True
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
     try:
      i2ca = int(self.taskdevicepluginconfig[0])
     except:
      i2ca = 0
     if i2ca>0:
      try:
       self.enc = miniencoder.request_menc_device(int(i2cl),i2ca)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Rotary I2C device requesting failed: "+str(e))
       self.initialized = False
       self.enc = None
     else:
       self.enc = None

   try:
    if float(self.uservar[0])<int(self.taskdevicepluginconfig[2]): # minvalue check
     self.set_value(1,self.taskdevicepluginconfig[2],False)
    if float(self.uservar[0])>int(self.taskdevicepluginconfig[3]): # maxvalue check
     self.set_value(1,self.taskdevicepluginconfig[3],False)
   except:
     self.set_value(1,self.taskdevicepluginconfig[2],False)
   if self.enabled and self.enc is not None:
         try:
           self.enc.lock = True
           self.enc.writeMax(int(float(self.taskdevicepluginconfig[3])))
           self.enc.writeMin(int(float(self.taskdevicepluginconfig[2])))
           self.enc.writeStep(int(float(self.taskdevicepluginconfig[1])))
           self.enc.writeCounter(int( float(self.uservar[0]) )) #sync stored init position
           self.enc.lock = False
           self.enc.onButtonPush = self.btn_handler
           self.enc.onButtonRelease = self.btn_handler
           self.enc.onChange = self.plugin_read
           self.enc.autoconfigInterrupt()
           self.initialized = True
           print("init done")
         except Exception as e:
           self.enc.lock = False
           print(e)

 def webform_load(self): # create html page for settings
  webserver.addFormPinSelect("Rotary interrupt pin","taskdevicepin0",self.taskdevicepin[0])
  webserver.addFormNote("Add one RPI INPUT pin to handle input changes immediately")
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x20","0x21","0x22","0x23","0x30","0x31","0x32","0x33"]
  optionvalues = [0x20,0x21,0x22,0x23,0x30,0x31,0x32,0x33]
  webserver.addFormSelector("I2C address","p219_addr",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")

  choice1 = int(float(self.taskdevicepluginconfig[1]))
  options = ["1","2","3","4"]
  optionvalues = [1,2,3,4]
  webserver.addFormSelector("Step","p219_step",len(options),options,optionvalues,None,choice1)
  try:
   minv = int(self.taskdevicepluginconfig[2])
  except:
   minv = 0
  webserver.addFormNumericBox("Limit min.","p219_min",minv,-65535,65535)
  try:
   maxv = int(self.taskdevicepluginconfig[3])
  except:
   maxv = 100
  if minv>=maxv:
   maxv = minv+1
  webserver.addFormNumericBox("Limit max.","p219_max",maxv,-65535,65535)
  if self.enc:
     try:
       eid = self.enc.readIDCode()
       ever = self.enc.readVersion()
       webserver.addFormNote("Rotary found. ID: "+str(eid)+" Version: "+str(ever))
     except Exception as e:
      print(e)
  return True

 def webform_save(self,params): # process settings post reply
   p1 = self.taskdevicepin[0]
   p2 = self.taskdevicepluginconfig[0]
   par = webserver.arg("p219_addr",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
   except:
    self.taskdevicepluginconfig[0] = 0
   try:
    self.taskdevicepin[0]=int(webserver.arg("taskdevicepin0",params))
   except:
    self.taskdevicepin[0]=-1

   try:
    self.taskdevicepluginconfig[1] = int(webserver.arg("p219_step",params))
   except:
    self.taskdevicepluginconfig[1] = 1
   try:
    self.taskdevicepluginconfig[2] = int(webserver.arg("p219_min",params))
   except:
    self.taskdevicepluginconfig[2] = 0
   par = webserver.arg("p219_max",params)
   if par == "":
    par = 100
   if int(self.taskdevicepluginconfig[2])>=int(par):
    par = int(self.taskdevicepluginconfig[2])+1
   try:
    self.taskdevicepluginconfig[3] = int(par)
   except:
    self.taskdevicepluginconfig[3] = 100

   if int(p1)!=int(self.taskdevicepin[0]) or int(p2)!=int(self.taskdevicepluginconfig[0]):
    self.plugin_init()

   return True

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled and self.readinprogress==0 and self.enc is not None and self.enc.lock==False:
    self.readinprogress = 1
    try:
     self.enc.lock = True
     bstat = int(self.enc.readStatus(0x02))
    except Exception as e:
     print("btn failed",e)
     bstat = 0
    try:
     cpos = self.enc.readCounter32()
     self.enc.lock = False
    except Exception as e:
     self.readinprogress=0
     self.enc.lock = False
     return False #retry?
    if cpos < int(self.taskdevicepluginconfig[2]): #enforce min limit
       cpos = int(self.taskdevicepluginconfig[2])
    if cpos > int(self.taskdevicepluginconfig[3]): #enforce max limit
       cpos = int(self.taskdevicepluginconfig[3])
    self.set_value(1,cpos,True)
    self.set_value(2,bstat,True)
    self._lastdataservetime = rpieTime.millis()
    self.readinprogress = 0
    result = True
  return result

 def timer_ten_per_second(self):
  if self.initialized and self.enabled:
     try:
      inval = gpios.HWPorts.input(int(self.taskdevicepin[0]))
     except:
      inval = -1
     if int(inval) != int(self.interruptval): #read state if interrupt pin changed
         self.p219_handler(0)
     self.interruptval = inval
     return self.timer100ms

 def btn_handler(self):
     self.plugin_read()

 def p219_handler(self,channel=0):
     tnow = rpieTime.millis()
     if self.enc:
      if self.enc.lock == False:
       self.enc.updateStatus()
       for t in range(0,len(Settings.Tasks)):
         if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)):
          if (Settings.Tasks[t].enabled and Settings.Tasks[t].taskindex != self.taskindex and Settings.Tasks[t].pluginid == self.pluginid):
            if int(Settings.Tasks[t].taskdevicepin[0]) == int(self.taskdevicepin[0]): #make sure if every rotary is notified on the same interrupt pin
             if tnow - Settings.Tasks[t]._lastdataservetime >= 100: #updated long time ago
                Settings.Tasks[t].plugin_read()
       self.enc.lock = False
