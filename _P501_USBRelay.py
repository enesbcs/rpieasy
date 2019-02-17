#!/usr/bin/env python3
#############################################################################
##################### USB Relay plugin for RPIEasy ##########################
#############################################################################
#
# Can be used on a simple PC or anything that runs Linux and has USB ports.
# Supports relays that uses the V-USB protocol.
# Based on: https://github.com/enesbcs/Very-Simple-USB-Relay
#
# It's an output device so can be controlled by controller through plugin_receivedata()
# or even with a simple taskvalueset command.
#
# Available commands: (for example http or rules based controlling)
#  usbrelay,relayname,relaynumber_on_panel,state
#  usbrelay,8978AB,1,0                             - Switch first relay at "8978AB" to LOW (0)
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import lib.lib_vusb as vusb

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 501
 PLUGIN_NAME = "Output - USBRelay"
 PLUGIN_VALUENAME1 = "Relay"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_USB
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.timeroption = True
  self.timeroptional = True

 def plugin_init(self,enableplugin=None):
  self.decimals[0]=0
  try:
   if (enableplugin==True and self.enabled==False) or (len(vusb.usbrelay.getcompatibledevlist())<1):
    vusb.vusb_force_refresh()
  except:
   pass
  plugin.PluginProto.plugin_init(self,enableplugin)
  success = False
  try:
   success = self.plugin_read()
  except Exception as e:
   success = False
  if success==False:
   self.initialized = False
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Unable to init USB relay!")
#   self.enabled = False
   self.set_value(1,0,True)

 def webform_load(self):
  choosendev = self.taskdevicepluginconfig[0]
  choosenrel = self.taskdevicepluginconfig[1]
  try:
   relaynum = vusb.usbrelay.getrelaynum()
  except:
   relaynum = 0
  try:
   relayids = vusb.usbrelay.getcompatibledevlist()
  except:
   relayids = []
  if relaynum>0 and len(relayids)>0:
   webserver.addHtml("<tr><td>Device ID:<td>")
   webserver.addSelector_Head("p501_relayname",True)
   for i in range(len(relayids)):
    webserver.addSelector_Item(relayids[i][2],relayids[i][2],(relayids[i][2]==choosendev),False)
   webserver.addSelector_Foot()

   webserver.addHtml("<tr><td>Relay number on device:<td>")
   webserver.addSelector_Head("p501_relaynum",True)
   for r in range(1,relaynum+1):
    webserver.addSelector_Item(r,r,(r==int(choosenrel)),False)
   webserver.addSelector_Foot()

  return True
  
 def webform_save(self,params):
  par = webserver.arg("p501_relayname",params)
  if par.strip() != "":
   self.taskdevicepluginconfig[0] = par
   par2 = webserver.arg("p501_relaynum",params)
   try:
    if int(par2)>0 and int(par2)<9:
     self.taskdevicepluginconfig[1] = par2
   except:
    pass
  return True
  
 def plugin_read(self):                   # Doing periodic status reporting
  res = False
  if self.initialized and self.enabled:
   try:
    vusb.usbrelay.initdevifneeded(self.taskdevicepluginconfig[0])
    swval = vusb.usbrelay.state(int(self.taskdevicepluginconfig[1]))
    res = True
   except:
    swval = 0
    res = False
   self.set_value(1,int(swval),True)
   self._lastdataservetime = rpieTime.millis()
  return res

 def plugin_receivedata(self,data):       # Watching for incoming mqtt commands
  if (len(data)>0):
   dstr = str(data[0]).lower()
   if 'on' in dstr or '1' in dstr or 'true' in dstr:
    swval = True
   else:
    swval = False
   if self.initialized and self.enabled:
    self.set_value(1,int(swval),False)
    vusb.usbrelay.initdevifneeded(self.taskdevicepluginconfig[0])
    vusb.usbrelay.state(int(self.taskdevicepluginconfig[1]),on=swval)

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized and self.enabled:
   try:
    vusb.usbrelay.initdevifneeded(self.taskdevicepluginconfig[0])
    vusb.usbrelay.state(int(self.taskdevicepluginconfig[1]),on=(str(value)==str(1)))
   except:
    pass
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "usbrelay":
   try:
    rname = cmdarr[1].strip()
    rnum  = int(cmdarr[2].strip())
    val   = int(cmdarr[3].strip())
   except:
    rname = ""
    rnum = 0
   if rname != "" and rname.lower() == self.taskdevicepluginconfig[0].lower():
    vusb.usbrelay.initdevifneeded(self.taskdevicepluginconfig[0])
    if rnum == int(self.taskdevicepluginconfig[1]):
     self.set_value(1,int(val),True)
     res = True
    else:
     vusb.usbrelay.state(int(self.taskdevicepluginconfig[1]),on=val)
  return res
