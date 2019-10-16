#!/usr/bin/env python3
#############################################################################
##################### IR Receiver plugin for RPIEasy ########################
#############################################################################
#
# This plugin made for LIRC compatible IR receivers.
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
 PLUGIN_ID = 16
 PLUGIN_NAME = "Communication - IR Receiver (TESTING)"
 PLUGIN_VALUENAME1 = "IR"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY # use lirc device, not gpio directly!
   self.vtype = rpieGlobals.SENSOR_TYPE_LONG
   self.readinprogress = 0
   self.valuecount = 1
   self.senddataoption = True
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.irdevice = None
   self.bgproc   = None
   self.enprot   = []

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
  if self.enabled==False:
   self.__del__()
   return False
  if self.uservar[0]!="0":
   self.uservar[0]="0"
  self.decimals[0]=0
  if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="":
   if self.enabled:
    try:
     self.irdevice = request_ir_device(self.taskdevicepluginconfig[0],True,self.receiver)
     self.initialized = self.irdevice.initialized
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LIRC device init error: ",+str(e))
   if self.initialized:
    try:
     pname = str(self.taskdevicepluginconfig[0]).split("/")
     self.ports = str(pname[-1])
    except:
     pass
    set_ir_protocols(self.enprot) #  print(enprot)
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"LIRC RX device initialized")
    self.bgproc = threading.Thread(target=self.irdevice.poller)
    self.bgproc.daemon = True
    self.bgproc.start()

 def receiver(self,proto,code):
     self.set_value(1,int(code,0),True)
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"IRSEND,"+str(proto)+","+str(code))
#     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Protocol: "+str(proto)+" Code: "+str(code))

 def webform_load(self):
  try:
   choice1 = self.taskdevicepluginconfig[0]
   options = find_lirc_devices()
   if len(options)>0:
    webserver.addHtml("<tr><td>LIRC device<td>")
    webserver.addSelector_Head("p016_dev",False)
    for o in range(len(options)):
     webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
    webserver.addSelector_Foot()
   else:
    webserver.addFormNote("/dev/lirc* not found")
    return False
   webserver.addFormNote("Select a receiver LIRC device (lirc-rx)! Do not forget to set the Data pin to IR-RX <a href='pinout'>at pinout settings</a>!")
  except Exception as e: 
   print(e)
  try:
   supprot = get_ir_supported_protocols()
   enprot  = get_ir_enabled_protocols()
   webserver.addRowLabel("Enabled protocols")
   for s in range(len(supprot)):
    webserver.addHtml("<label class='container' style='height:30px'>"+supprot[s]+" <input type='checkbox' id='")
    webserver.addHtml("_"+supprot[s]+"' name='_"+supprot[s]+"'")
    if (supprot[s] in enprot):
     webserver.addHtml(" checked")
    webserver.addHtml("><span class='checkmark'></span></label>")
  except Exception as e:
   print(e)
  return True

 def webform_save(self,params):
  par = webserver.arg("p016_dev",params)
  self.taskdevicepluginconfig[0] = str(par)
  self.enprot = []
  try:
   for k,v in params.items():
    if k[0]=="_":
     if v=="on":
      self.enprot.append(k[1:])
  except Exception as e:
   print(e)
#  set_ir_protocols(self.enprot) #  print(enprot)
  self.plugin_init()
  return True

