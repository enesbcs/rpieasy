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
import commands
import threading
import Settings

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
  self.trigger = False
  self.timer100ms = False
  self.prevval = -1

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  self.trigger = False
  self.timer100ms = False
  self.prevval = -1
  if self.enabled:
   self.initialized = True
#   self.set_value(1,0,False) # init with 0 cmd!
   if not(str(self.taskdevicepluginconfig[4]) in ["_","0",""]):
    self.trigger = True
    self.timer100ms = True

 def webform_load(self):
  webserver.addFormTextBox("Command 0","plugin_511_cmd0",str(self.taskdevicepluginconfig[0]),512)
  webserver.addFormTextBox("Command 1","plugin_511_cmd1",str(self.taskdevicepluginconfig[1]),512)
  webserver.addFormNote("Specify OS commands that has to be executed at the speficied state (0/1)")
  webserver.addFormCheckBox("Use threading to run in background","plugin_511_th",self.taskdevicepluginconfig[2])
  webserver.addFormCheckBox("Enable parsing command line before execute","plugin_511_parse",self.taskdevicepluginconfig[3])

  options2 = ["None"]
  optionvalues2 = ["_"]
  for t in range(0,len(Settings.Tasks)):
      if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)) and (t != self.taskindex):
       for v in range(0,Settings.Tasks[t].valuecount):
        options2.append("T"+str(t+1)+"-"+str(v+1)+" / "+str(Settings.Tasks[t].taskname)+"-"+str(Settings.Tasks[t].valuenames[v]))
        optionvalues2.append(str(t)+"_"+str(v))
  webserver.addHtml("<tr><td>Trigger variable:<td>")
  webserver.addSelector_Head("p511_trigger",False)
  ddata = str(self.taskdevicepluginconfig[4])
  for o in range(len(options2)):
   webserver.addSelector_Item(options2[o],optionvalues2[o],(str(optionvalues2[o])==str(ddata)),False)
  webserver.addSelector_Foot()
  webserver.addFormNumericBox("Trigger Low value","p511_low",self.taskdevicepluginconfig[5],-65535,65535)
  webserver.addFormNumericBox("Trigger High value","p511_high",self.taskdevicepluginconfig[6],-65535,65535)
  return True

 def webform_save(self,params):
  self.taskdevicepluginconfig[0] = str(webserver.arg("plugin_511_cmd0",params)).strip()
  self.taskdevicepluginconfig[1] = str(webserver.arg("plugin_511_cmd1",params)).strip()
  if str(self.taskdevicepluginconfig[0])=="0":
   self.taskdevicepluginconfig[0]=""
  if str(self.taskdevicepluginconfig[1])=="0":
   self.taskdevicepluginconfig[1]=""
  self.taskdevicepluginconfig[2] = (webserver.arg("plugin_511_th",params)=="on")
  self.taskdevicepluginconfig[3] = (webserver.arg("plugin_511_parse",params)=="on")
  self.taskdevicepluginconfig[4] = str(webserver.arg("p511_trigger",params))
  try:
   self.taskdevicepluginconfig[5] = int(webserver.arg("p511_low",params))
  except:
   self.taskdevicepluginconfig[5] = 0
  try:
   self.taskdevicepluginconfig[6] = int(webserver.arg("p511_high",params))
  except:
   self.taskdevicepluginconfig[6] = 1
  if str(self.taskdevicepluginconfig[4]) in ["_","0",""]:
    self.trigger = False
    self.timer100ms = False
  else:
    self.trigger = True
    self.timer100ms = True
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
      cmdline = self.taskdevicepluginconfig[val2]
      if self.taskdevicepluginconfig[3]:
       cl, st = commands.parseruleline(cmdline)
       if st=="CMD":
          cmdline = str(cl)
       else:
          cmdline = str(cmdline)
      output = os.popen(cmdline)
      if self.taskdevicepluginconfig[2]:
       return True
      res = ""
      for l in output:
       res += str(l)
     else:
      return None
  return res

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  res = False
  if self.initialized and self.enabled:
    if 'on' in str(value).lower() or str(value)=="1":
     val = 1
    else:
     val = 0
    try:
     if self.taskdevicepluginconfig[2]:
      res = True
      bgt = threading.Thread(target=self.runcmd, args=(val,))
      bgt.daemon = True
      bgt.start()
     else:
      res = self.runcmd(val)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
     res = False
  if res is not None and res!=False:
    if self.taskdevicepluginconfig[2]:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"OS command started at background")
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG_MORE,str(res))
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"OS command executed succesfully")
  else:
    if res==False:
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

 def timer_ten_per_second(self):
   try:
    if self.trigger:
     tid = str(self.taskdevicepluginconfig[4])
     ti = tid.split("_")
     tasknum = int(ti[0])
     valnum  = int(ti[1])
     aval = int(Settings.Tasks[tasknum].uservar[valnum])
     if aval != self.prevval:
      if aval <= int(self.taskdevicepluginconfig[5]):
       self.set_value(1,0,False)
      elif aval >= int(self.taskdevicepluginconfig[6]):
       self.set_value(1,1,False)
      self.prevval = aval
   except:
    pass
   return self.timer100ms
