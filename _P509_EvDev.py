#!/usr/bin/env python3
#############################################################################
################## Generic EvDev input plugin for RPIEasy ###################
#############################################################################
#
# Read raw values from generic linux evdev devices, such as joystick, keypad...
# Device can be selected from /dev/input/event*
# Tested with Bluetooth VRBOX keypad
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import threading
import struct
import time
import glob

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 509
 PLUGIN_NAME = "Input - Generic EvDev (TESTING)"
 PLUGIN_VALUENAME1 = "Data"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
   self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
   self.readinprogress = 0
   self.valuecount = 1
   self.senddataoption = True
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.bgproc = None
   self.evdev = None
   self.timeout = 0.001

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.ports = 0
  if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="":
   if self.enabled:
    try:
     self.evdev = open(str(self.taskdevicepluginconfig[0]),"rb")
     self.initialized = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EVDEV open error: "+str(e))
     self.initialized = False
    if self.initialized:
     try:
      pname = str(self.taskdevicepluginconfig[0]).split("/")
      self.ports = str(pname[-1])
     except:
      pass
     self.bgproc = threading.Thread(target=self.bgreceiver)
     self.bgproc.daemon = True
     self.bgproc.start()
   else:
    self.initialized = False

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = self.get_evdevs()
  if len(options)>0:
   webserver.addHtml("<tr><td>EvDev Device:<td>")
   webserver.addSelector_Head("p509_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()
  else:
   webserver.addFormNote("/dev/input/event* not found")
  return True

 def webform_save(self,params):
  par = webserver.arg("p509_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
  self.plugin_init()
  return True

 def bgreceiver(self):
  cr=-1
  pcr = -1
  pval = 0
  while self.enabled:
   try:
    data = self.evdev.read(16)
    tdata =struct.unpack('2IHHI',data)
   except:
    cr=-1
   if len(tdata)>4:
    if tdata[2] == 1: # pos2: EV_KEY=1, EV_MSC=4
     cr=tdata[3]      # pos3: KEYCODE, pos4: value 1=pressed,0=released,2=continously pressed
     if (cr!=pcr) or (pval!=tdata[4]):
      self.set_value(1,cr,True)
      pcr=cr
      pval = 0
   time.sleep(self.timeout)

 def get_evdevs(self):
  rlist = []
  try:
   rlist = glob.glob('/dev/input/event*')
  except:
   rlist = []
  return rlist
