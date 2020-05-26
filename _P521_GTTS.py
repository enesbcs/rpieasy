#!/usr/bin/env python3
#############################################################################
############# Google TTS PyGame Sound Player plugin for RPIEasy #############
#############################################################################
#
# Can be controlled by plugin_receivedata()
# TEXT device with one input parameter: one line text
#
# If sound device is currently used by other plugin, it will be asked to stop.
#
# Available commands:
#  say,texttospeeech        - Converts text to speech than play it
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import Settings
import pygame
import time
import gtts # pip3 install gtts
from io import BytesIO

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 521
 PLUGIN_NAME = "Output - Google TTS Sound Player"
 PLUGIN_VALUENAME1 = "Text"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SND
  self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.timeroption = False
  self.playing = False
  self.languages = []
  self.lang = 'en'

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0] = 0
  if Settings.SoundSystem["usable"]==False:
   self.initialized = False
   self.enabled = False
  else:
   self.initialized = True
  self.stop(True)

 def webform_load(self):
  if Settings.SoundSystem["usable"]==False:
   webserver.addHtml("<tr><td><td><font color='red'>The sound system can not be used!</font>")
  else:
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Getting language list")
   if len(self.languages)<1:
    try:
     self.languages = gtts.lang.tts_langs()
    except Exception as e:
     self.languages = []
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   try:
    options = []
    optionvalues = []
    if len(self.languages)>0:
     for l in self.languages:
      options.append(l+" "+self.languages[l])
      optionvalues.append(l)
    webserver.addHtml("<tr><td>Language:<td>")
    webserver.addSelector_Head("p521_lang",False)
    for o in range(len(options)):
     try:
      webserver.addSelector_Item(options[o],optionvalues[o],(str(optionvalues[o])==str(self.lang)),False)
     except Exception as e:
      print(e)
    webserver.addSelector_Foot()
   except Exception as e:
    print(e)
   webserver.addFormNote("Either taskvalueset or say command can be used to speak text.")
  return True

 def webform_save(self,params):
  try:
   par = webserver.arg("p521_lang",params)
   if par=="" or par=="0":
    self.lang = 'en'
   else:
    self.lang = str(par)
  except:
   self.lang = 'en'
  return True

 def plugin_receivedata(self,data):       # Watching for incoming mqtt commands
  if (len(data)>0):
   try:
    self.set_value(1,str(data[0]),False)
   except Exception as e:
    print(str(e))

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized:
   self.play(value)
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)
 
 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "say":
   try:
    rname = cmd[4:].strip()
   except:
    rname = ""
   if rname != "":
    self.set_value(1,str(rname),True)
    res = True
  return res

 def play(self,text):
   if (Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] != self.taskindex) and (text!=""):
    if Settings.SoundSystem["askplugintorelease"] != None:
     try:
      Settings.SoundSystem["askplugintorelease"](True) # ask to stop
     except Exception as e:
      print(e) # DEBUG
   if (Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] == self.taskindex) or (self.playing):
    if text=="":
     return False
    self.stop(False)
   if Settings.SoundSystem["inuse"]: # endless loop? condition to exit?
    time.sleep(0.2)
   if Settings.SoundSystem["inuse"]==False:
     try:
      tts = gtts.gTTS(text=text, lang=self.lang)
      fp = BytesIO()
      tts.write_to_fp(fp)
      fp.seek(0)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
      return False
     try:
      pygame.mixer.init()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
      return False
     Settings.SoundSystem["inuse"] = True
     Settings.SoundSystem["usingplugintaskindex"] = self.taskindex
     Settings.SoundSystem["askplugintorelease"] = self.stop
     try:
       pygame.mixer.music.load(fp)
       self.playing=True
     except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
     if self.playing: 
       pygame.mixer.music.play()
#       while self.playing and pygame.mixer.music.get_busy():
#        pygame.time.Clock().tick(10)
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
   plugin.PluginProto.set_value(self,1,"")
  self.playing = False

 def plugin_exit(self):
  self.stop(True)
  return True
