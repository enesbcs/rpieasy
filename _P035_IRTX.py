#!/usr/bin/env python3
#############################################################################
##################### IR Transmitter plugin for RPIEasy #####################
#############################################################################
#
# This plugin made for LIRC compatible IR transceivers.
# GPIO-IR-TX provides unstable output, PWM-IR-TX has to be better, but not works to me at all.
#
# Available commands:
#
#  IRSEND: That commands format is: IRSEND,<protocol>,<data>,<bits>,<repeat>
#          bits and repeat default to 0 if not used and they are optional
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import threading
from lib.lib_ir import *

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 35
 PLUGIN_NAME = "Communication - IR Transmit (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "IR"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY # use lirc device, not gpio directly!
   self.vtype = rpieGlobals.SENSOR_TYPE_NONE
   self.readinprogress = 0
   self.valuecount = 0
   self.senddataoption = False
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.irdevice = None

 def __del__(self):
  try:
   self.initialized = False
   if self.irdevice is not None:
    self.irdevice.stop()
  except:
   pass

 def plugin_exit(self):
  self.__del__()

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = False
  if self.uservar[0]!="0":
   self.uservar[0]="0"
  self.decimals[0]=0
  if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="":
   if self.enabled:
    try:
     self.irdevice = request_ir_device(self.taskdevicepluginconfig[0],False)
     self.initialized = self.irdevice.initialized
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LIRC device init error: ",+str(e))
   if self.initialized:
    try:
     pname = str(self.taskdevicepluginconfig[0]).split("/")
     self.ports = str(pname[-1])
    except:
     pass
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"LIRC TX device initialized")

 def webform_load(self):
  try:
   choice1 = self.taskdevicepluginconfig[0]
   options = find_lirc_devices()
   if len(options)>0:
    webserver.addHtml("<tr><td>LIRC device<td>")
    webserver.addSelector_Head("p035_dev",False)
    for o in range(len(options)):
     webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
    webserver.addSelector_Foot()
   else:
    webserver.addFormNote("/dev/lirc* not found")
    return False
   webserver.addFormNote("Select a transceiver LIRC device (lirc-tx)! Do not forget to set the Data pin to IR-PWM or IR-TX <a href='pinout'>at pinout settings</a>!")
   webserver.addFormNote("According to documentation, only GPIO18 or GPIO12 is supported as IR-PWM!")
  except Exception as e: 
   print(e)
  return True

 def webform_save(self,params):
  par = webserver.arg("p035_dev",params)
  self.taskdevicepluginconfig[0] = str(par)
  self.plugin_init()
  return True

 def plugin_write(self,cmd):
  res = False
  if self.initialized == False or self.enabled==False:
   return False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "irsend":
   prot = ""
   data = -1
   bits = 8
   repeat = 1
   try:
    prot = str(cmdarr[1].strip()).upper()
    data = int(cmdarr[2].strip(),0)
   except:
    pass
   try:
    bits = int(cmdarr[3].strip())
   except:
    bits = data.bit_length()
   try:
    repeat = int(cmdarr[4].strip())
   except:
    repeat = 1
   if prot!="" and data>-1:
    protonum = get_protonum(prot,bits)
#    print(prot,bits,protonum)
    if protonum != -1:
     while repeat>0:
      res = self.irdevice.irsend(data,protonum)
      time.sleep(1)
      repeat=repeat-1
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"IRTX code sent "+str(hex(data))+" (protocoll:"+get_protoname(protonum)+")")
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Unknown protocol "+str(prot))
  return res
