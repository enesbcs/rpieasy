#############################################################################
####################### SnapClient plugin for RPIEasy #######################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import Settings
import os
import linux_os as OS # subprocess
import time
import signal

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 525
 PLUGIN_NAME = "Output - SnapClient control"
 PLUGIN_VALUENAME1 = "Enabled"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SND
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.timeroption = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  if Settings.SoundSystem["usable"]==False:
   self.initialized = False
   self.enabled = False
   self.uservar[0]=0
  else:
   if self.taskdevicepluginconfig[0]==0:
    if self.getstatus():
     self.play(1)
   elif self.taskdevicepluginconfig[0]==1:
    self.stop()
   elif self.taskdevicepluginconfig[0]==2:
    self.play(1)


 def webform_load(self):
  if Settings.SoundSystem["usable"]==False:
   webserver.addHtml("<tr><td><td><font color='red'>The sound system can not be used!</font>")
  else:
   webserver.addFormNote("Download <a href='https://github.com/badaix/snapcast/releases/latest'>latest snapclient</a> manually and install to your system! (armhf=Raspberry, amd64=x64 PC)")
   webserver.addFormNote("Enable/disable snapclient receiver - if snapclient started its blocking Alsa from other PyGame based sound plugins!")
   optionvalues = [0,1,2]
   options = ["No change","Stop","Start"]
   webserver.addFormSelector("Change state at plugin init","p525_stat",len(options),options,optionvalues,None,self.taskdevicepluginconfig[0])
  return True

 def webform_save(self,params):
  try:
   self.taskdevicepluginconfig[0] = int(webserver.arg("p525_stat",params))
  except:
   self.taskdevicepluginconfig[0] = 0
  return True

 def plugin_receivedata(self,data):       # Watching for incoming mqtt commands
  if (len(data)>0):
#   print(data)
   self.set_value(1,int(data[0]),False)

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized and self.enabled:
   self.play(value)
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def getstatus(self):
     status = False
     try:
      output = os.popen(OS.cmdline_rootcorrect('sudo systemctl is-active snapclient'))
      for line in output:
       if line.strip().startswith("active"):
        status = True
     except Exception as e:
      print(e)
     self.uservar[0]=int(status)
     return status

 def play(self,level):
   try:
    level = int(level)
   except:
    level = 0
   if level==1:
    if (Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] != self.taskindex):
     if Settings.SoundSystem["askplugintorelease"] != None:
      try:
       Settings.SoundSystem["askplugintorelease"](True) # ask to stop
      except Exception as e:
       pass
      time.sleep(0.2)
    try:
      output = os.popen(OS.cmdline_rootcorrect('sudo systemctl start snapclient'))
      for line in output:
       pass
    except:
      pass
    state = self.getstatus()
    if state==1:
     Settings.SoundSystem["inuse"] = True
     Settings.SoundSystem["usingplugintaskindex"] = self.taskindex
     Settings.SoundSystem["askplugintorelease"] = self.stop
   else:
     self.stop()

 def stop(self,AddEvent=False):
  if int(self.uservar[0])>0:
    try:
      output = os.popen(OS.cmdline_rootcorrect('sudo systemctl stop snapclient'))
      for line in output:
       pass
    except:
      pass
    if Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] == self.taskindex:
     Settings.SoundSystem["inuse"] = False
     Settings.SoundSystem["usingplugintaskindex"] = -1
     Settings.SoundSystem["askplugintorelease"] = None
    self.getstatus()
    if AddEvent:
     plugin.PluginProto.set_value(self,1,0)

