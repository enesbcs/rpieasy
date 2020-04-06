#!/usr/bin/env python3
#############################################################################
################# OS command runner plugin for RPIEasy ######################
#############################################################################
#
# Two way communication is implemented through plugin_receivedata()
# Runs first command when state is 0 and runs second command when state is 1. (off/on)
# Defaults to off at initialization.
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import misc
import os

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 511
 PLUGIN_NAME = "Generic - Run OS Command"
 PLUGIN_VALUENAME1 = "State"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.pullupoption = False
  self.inverselogicoption = True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  if self.enabled:
   self.initialized = True
   self.set_value(1,0,False) # init with 0 cmd!

 def webform_load(self):
  webserver.addFormTextBox("Command 0","plugin_511_cmd0",str(self.taskdevicepluginconfig[0]),512)
  webserver.addFormTextBox("Command 1","plugin_511_cmd1",str(self.taskdevicepluginconfig[1]),512)
  webserver.addFormNote("Specify OS commands that has to be executed at the speficied state (0/1)")
  return True

 def webform_save(self,params):
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_511_cmd0",params)).strip()
  self.taskdevicepluginconfig[1] = str(webserver.arg("plugin_511_cmd1",params)).strip()
  if str(self.taskdevicepluginconfig[0])=="0":
   self.taskdevicepluginconfig[0]=""
  if str(self.taskdevicepluginconfig[1])=="0":
   self.taskdevicepluginconfig[1]=""
  return True

 def runcmd(self,number): # run command stored at taskdevicepluginconfig[number]
  res = False
  if self.enabled:
    number=int(number)
    if self.pininversed: # inverse handled inside parent set_value, that is called after runcmd, so take care, before run
     val2=(1-number)
    else:
     val2=number
    if val2>=0 and val2<=1:
     if self.taskdevicepluginconfig[val2]!="" and str(self.taskdevicepluginconfig[val2])!="0":
      output = os.popen(self.taskdevicepluginconfig[val2])
      res = ""
      for l in output:
       res += str(l)
  return res

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  res = False
  if self.initialized and self.enabled:
    if 'on' in str(value).lower() or str(value)=="1":
     val = 1
    else:
     val = 0
    try:
     res = self.runcmd(val)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
     res = False
  if res!=False:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE,str(res))
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"OS command executed succesfully")
  else:
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"OS command execution failed")
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def plugin_receivedata(self,data):                        # set value based on mqtt input
  if (len(data)>0) and self.initialized and self.enabled:
   if 'on' in str(data[0]).lower() or str(data[0])=="1":
    val = 1
   else:
    val = 0
   self.set_value(1,val,False)
#  print("Data received:",data) # DEBUG
