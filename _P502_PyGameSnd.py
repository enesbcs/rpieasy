#!/usr/bin/env python3
#############################################################################
##################### PyGame Sound Player plugin for RPIEasy ################
#############################################################################
#
# Can be controlled by plugin_receivedata() like a DIMMER device - Selector Switch
# The sound file associated with the selected level will be played using the PyGame
# sound engine.
# If sound device is currently used by other plugin, it will be asked to stop.
#
# Available commands:
#  playaudio,taskname,10        - Plays the sound file associated with level 10
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import Settings
import pygame
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 502
 PLUGIN_NAME = "Output - PyGame Sound Player"
 PLUGIN_VALUENAME1 = "SoundID"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SND
  self.vtype = rpieGlobals.SENSOR_TYPE_DIMMER
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.timeroption = False
  self.playing = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  if Settings.SoundSystem["usable"]==False:
   self.initialized = False
   self.enabled = False
  self.stop(True)

 def webform_load(self):
  if Settings.SoundSystem["usable"]==False:
   webserver.addHtml("<tr><td><td><font color='red'>The sound system can not be used!</font>")
  else:
   maxlevel = rpieGlobals.PLUGIN_CONFIGVAR_MAX
   if maxlevel>10:
    maxlevel = 10
   for c in range(1,maxlevel+1):
    webserver.addFormTextBox("Level "+str(c*10),"p502_lvl_"+str(c*10),str(self.taskdevicepluginconfig[c]),120)
    webserver.addBrowseButton("Browse","p502_lvl_"+str(c*10),startdir=str(self.taskdevicepluginconfig[c]))
   webserver.addFormNote("Specify file names with relative pathname for every level, that is needed!")
  return True

 def webform_save(self,params):
  maxlevel = rpieGlobals.PLUGIN_CONFIGVAR_MAX
  if maxlevel>10:
   maxlevel = 10
  for c in range(1,maxlevel+1):
   try:
    par = webserver.arg("p502_lvl_"+str(c*10),params)
    if par.strip() != "":
     self.taskdevicepluginconfig[c] = par
   except:
    pass
  return True

 def plugin_receivedata(self,data):       # Watching for incoming mqtt commands
  if (len(data)>0):
#   print(data)
   self.set_value(1,int(data[0]),False)

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized:
   self.play(value)
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)
 
 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "playaudio":
   try:
    rname = cmdarr[1].strip()
    rnum  = int(cmdarr[2].strip())
   except:
    rname = ""
    rnum = 0
   if rname != "" and rname.lower() == self.taskname.lower():
    self.set_value(1,int(rnum),True)
    res = True
  return res

 def play(self,level): # 0,10,20,30,40,50,60,70
   level = int(level)
   if (Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] != self.taskindex) and (level>0):
    if Settings.SoundSystem["askplugintorelease"] != None:
     try:
      Settings.SoundSystem["askplugintorelease"](True) # ask to stop
     except Exception as e:
      print(e) # DEBUG
   if (Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] == self.taskindex) or (self.playing):
    self.stop(False)
    if level<10:
     return False
   if Settings.SoundSystem["inuse"]: # endless loop? condition to exit?
    time.sleep(0.2)
   if Settings.SoundSystem["inuse"]==False:
    if level == "" or level<10:
     self.stop(False)
     return False
    elif level>9:
     sfx = round(level / 10)
     try:
      pygame.mixer.init()
     except:
      return False
     Settings.SoundSystem["inuse"] = True
     Settings.SoundSystem["usingplugintaskindex"] = self.taskindex
     Settings.SoundSystem["askplugintorelease"] = self.stop
     fname = ""
     try:
      fname = self.taskdevicepluginconfig[sfx]
     except:
      fname = ""
     if fname != "" and fname != 0:
      try:
       pygame.mixer.music.load(fname)
       self.playing=True
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
      if self.playing: 
       pygame.mixer.music.play(-1)
   return self.playing

 def stop(self,AddEvent=False):
  if Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] == self.taskindex:
   try:
    if pygame.mixer.get_init():
     if pygame.mixer.music.get_busy():
      pygame.mixer.music.stop()
     pygame.mixer.quit()
   except:
    pass
   Settings.SoundSystem["inuse"] = False
   Settings.SoundSystem["usingplugintaskindex"] = -1
   Settings.SoundSystem["askplugintorelease"] = None
  if AddEvent:
   plugin.PluginProto.set_value(self,1,0)
  self.playing = False

 def plugin_exit(self):
  self.stop(True)
  return True
