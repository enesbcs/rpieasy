#!/usr/bin/env python3
#############################################################################
####################### USB Temper plugin for RPIEasy #######################
#############################################################################
#
# Based on Pham Urwen's temper script
#  https://github.com/urwen/temper/
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import lib.lib_temper as utemper

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 508
 PLUGIN_NAME = "Environment - USB Temper"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Humidity"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_USB
  self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
  self.readinprogress = 0
  self.valuecount = 2
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self._lastdataservetime = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.initialized = False
  if str(self.taskdevicepluginconfig[0])=="0" or str(self.taskdevicepluginconfig[0]).strip()=="":
   if self.enabled or enableplugin:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"No device selected")
   self.enabled = False
   return False
  if enableplugin!=False:
   try:
    utemper.force_temper_detect()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Temper error: "+str(e))
  if len(utemper.get_temper_list())>0:
   if self.enabled or enableplugin:
    self.initialized = True
    self.ports = str(self.taskdevicepluginconfig[0])
    if self.interval>2:
     nextr = self.interval-2
    else:
     nextr = self.interval
    self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    self.set_value(2,0,False)
    if self.taskdevicepluginconfig[1] in [0,1]:
     self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
     self.valuecount = 1
    elif self.taskdevicepluginconfig[1] in [2,3]:
     self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM
     self.valuecount = 2
   else:
    self.ports = ""
  else:
   self.enabled = False

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  try:
   options = utemper.get_select_list()
  except:
   options = []
  if len(options)>0:
   webserver.addHtml("<tr><td>Device:<td>")
   webserver.addSelector_Head("p508_addr",True)
   for o in range(len(options)):
    webserver.addSelector_Item(str(options[o][1])+" "+str(options[o][2]),int(o+1),(str(o+1)==str(choice1)),False)
   webserver.addSelector_Foot()
   choice2 = self.taskdevicepluginconfig[1]
   options = ["Internal temp","External temp", "Internal temp+humidity", "External temp+humidity"]
   optionvalues = [0,1,2,3]
   webserver.addFormSelector("Sensor type","p508_type",len(optionvalues),options,optionvalues,None,choice2)
  webserver.addFormNote("Without root rights you will not see any Temper device!")
  return True

 def webform_save(self,params):
  try:
   par = webserver.arg("p508_addr",params)
   self.taskdevicepluginconfig[0] = int(par)
  except:
   self.taskdevicepluginconfig[0] = ""
  try:
   par = webserver.arg("p508_type",params)
   self.taskdevicepluginconfig[1] = int(par)
  except:
   self.taskdevicepluginconfig[1] = 0
  self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
    self.readinprogress = 1
    suc = False
    try:
     rd = utemper.get_temper_list()
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Temper read error! Trying to reread. ("+str(e)+")")
     rd = []
    if len(rd)>0:
     da = int(self.taskdevicepluginconfig[0])
     if da>0:
      da = da-1
     if da>=len(rd):
      da = len(rd)-1
     tval = self.get_value(rd[da])
     if tval[2]>0:
      self.set_value(1,tval[0],False)
      self._lastdataservetime = rpieTime.millis()
      suc = True
     if tval[2]>1:
      self.set_value(2,tval[1],False)
     self.plugin_senddata()
    if suc==False:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Temper read error!")
    result = True
    self.readinprogress = 0
  return result

 def get_value(self,datarr):
  resarr = [0,0,0]
  if self.taskdevicepluginconfig[1] in [0,2]:
   try:
    resarr[0]=float(datarr["internal temperature"])
    resarr[2]=1
   except:
    resarr[0]=0
  elif self.taskdevicepluginconfig[1] in [1,3]:
   try:
    resarr[0]=float(datarr["external temperature"])
    resarr[2]=1
   except:
    resarr[0]=0
  if self.taskdevicepluginconfig[1]==2:
   try:
    resarr[1]=float(datarr["internal humidity"])
    resarr[2]=2
   except:
    resarr[1]=0
  elif self.taskdevicepluginconfig[1]==3:
   try:
    resarr[1]=float(datarr["external humidity"])
    resarr[2]=2
   except:
    resarr[1]=0
  return resarr
