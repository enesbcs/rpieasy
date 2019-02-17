#!/usr/bin/env python3
#############################################################################
################# 433Mhz RF Transmitter plugin for RPIEasy ##################
#############################################################################
#
# This plugin made for simple one GPIO based RF transceivers.
#
# RF433 sender plugin based on rc-switch:
#  https://github.com/sui77/rc-switch
#
# Available commands:
#  RFSEND,<binary_code>                 - binary code like 01010101
#  RFSENDDEC,<decimal_code>,<bitlength> - decimal code like 5393, bit length is optional: default is 24
#  RFPROTOCOL,<protocol_number>         - protocol number can be from 1 to 7
#  RFREPEAT,<number>                    - repeat msg specific times
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
from lib.lib_rcswitch import *

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 112
 PLUGIN_NAME = "Communication - RF433 Transmitter (TESTING)"
 PLUGIN_VALUENAME1 = "Value1"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SINGLE
   self.vtype = rpieGlobals.SENSOR_TYPE_NONE
   self.readinprogress = 0
   self.valuecount = 0
   self.senddataoption = False
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.rfdevice  = None
   self.protocol  = 1
   self.bitlength = 24
   self.repeat    = 3

 def __del__(self):
  try:
   self.initialized = False
   if self.rfdevice is not None:
    self.rfdevice.disableTransmit()
  except:
   pass

 def plugin_exit(self):
  self.__del__()

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.rfinit()

#  if self.initialized == False:
#     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RF433 init failed")

 def rfinit(self):
   if int(self.taskdevicepin[0])>=0 and self.enabled:
    try:
      self.rfdevice = getRFDev(False)
      pval = self.rfdevice.initpin()
      if self.rfdevice and int(pval)>0:
       self.initialized = True
       self.protocol  = int(self.taskdevicepluginconfig[0])
       self.bitlength = int(self.taskdevicepluginconfig[1])
       self.repeat    = int(self.taskdevicepluginconfig[2])
       self.rfdevice.setProtocol(self.protocol)
       self.rfdevice.setRepeatTransmit(self.repeat)
       self.rfdevice.enableTransmit(int(self.taskdevicepin[0]))
    except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RF433: "+str(e))
      self.initialized = False
   else:
      self.initialized = False

 def webform_load(self):
   webserver.addFormNote("Select an output pin.")
   prot = self.taskdevicepluginconfig[0]
   try:
    prot = int(prot)
   except:
    prot = 0
   if prot == 0:
    prot = 1
   options = ["1","2","3","4","5","6","7"]
   optionvalues = [1,2,3,4,5,6,7]
   webserver.addFormSelector("Protocol","p112_prot",len(options),options,optionvalues,None,prot)
   webserver.addFormNote("Default is 1")
   bits = self.taskdevicepluginconfig[1]
   try:
    bits = int(bits)
   except:
    bits = 0
   if bits == 0:
    bits = 24
   webserver.addFormNumericBox("Data bits","p112_bits",bits,1,64)
   webserver.addFormNote("Default is 24")
   rep = self.taskdevicepluginconfig[2]
   try:
    rep = int(rep)
   except:
    rep = 0
   if rep == 0:
    rep = 3
   webserver.addFormNumericBox("Repeat","p112_rep",rep,1,20)
   webserver.addFormNote("Default is 3")
   return True

 def webform_save(self,params):
  par = webserver.arg("p112_prot",params)
  if par == "":
   par = 0
  if par == 0:
   par = 1
  self.taskdevicepluginconfig[0] = int(par)
  par = webserver.arg("p112_bits",params)
  if par == "":
   par = 0
  if par == 0:
   par = 24
  self.taskdevicepluginconfig[1] = int(par)
  par = webserver.arg("p112_rep",params)
  if par == "":
   par = 0
  if par == 0:
   par = 3
  self.taskdevicepluginconfig[2] = int(par)

  self.rfinit()
  return True

 def plugin_write(self,cmd):
  res = False
  if self.initialized == False:
   return False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "rfprotocol":
   par1 = -1
   try:
    par1 = int(cmdarr[1].strip())
   except:
    par1 = -1
   if par1>0 and par1<8:
    if par1 != self.protocol:
     self.protocol = par1
     self.rfdevice.setProtocol(self.protocol)
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"RF protocol set to "+str(par1))
     res = True
  elif cmdarr[0] == "rfrepeat":
   par1 = -1
   try:
    par1 = int(cmdarr[1].strip())
   except:
    par1 = -1
   if par1>0 and par1<21:
    if par1 != self.repeat:
     self.repeat = par1
     self.rfdevice.setRepeatTransmit(self.repeat)
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"RF repeat set to "+str(par1))
     res = True
  elif cmdarr[0] == "rfsend":
   par1 = -1
   try:
    par1 = str(cmdarr[1].strip())
   except:
    par1 = ""
   if len(par1)>0:
    self.rfdevice.send_binstr(par1)
    res = True
  elif cmdarr[0] == "rfsenddec":
   par1 = -1
   try:
    par1 = int(cmdarr[1].strip())
   except Exception as e:
    par1 = 0
   par2 = self.bitlength
   try:
    par2 = int(cmdarr[2].strip())
   except Exception as e:
    par2 = self.bitlength
   if par1>0:
    self.rfdevice.send(par1,par2)
    res = True
  return res
