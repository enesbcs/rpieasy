#############################################################################
############# PyGame Background Sound Player plugin for RPIEasy #############
#############################################################################
#
# Can be controlled by plugin_receivedata() sending a file name (not number!)
# which is not exactly ESPEasy compatible but with Domoticz it is absolutely
# usable through a TEXT device.
#
# TEXT can be filled with file names with comma separated, but only file names
# extension is automatically added as .mp3. Files will be played in the background
# one after another.
#
# Available command:
#  playaudiobg,taskname,cardrefused,retry,alarm
#            - Plays cardrefused.mp3 then retry.mp3
#              then alarm.mp3 in the specified directory
#
# If sound device is currently used by other plugin, it will be asked to stop.
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
import threading

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 503
 PLUGIN_NAME = "Output - PyGame Sound Background Player"
 PLUGIN_VALUENAME1 = "Names"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SND
  self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.timeroption = False
  self.playing = False
  self.sndthread = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if Settings.SoundSystem["usable"]==False:
   self.initialized = False
   self.enabled = False
  self.sndthread = None
  self.stop()

 def webform_load(self):
  if Settings.SoundSystem["usable"]==False:
   webserver.addHtml("<tr><td><td><font color='red'>The sound system can not be used!</font>")
  else:
   webserver.addFormTextBox("Directory","p503_dir",str(self.taskdevicepluginconfig[0]),120)
   webserver.addBrowseButton("Browse","p503_dir",startdir=str(self.taskdevicepluginconfig[0]))
   webserver.addFormNote("Specify directory where .MP3 files located!")
  return True

 def webform_save(self,params):
  par = webserver.arg("p503_dir",params).strip()
  if par != "":
   self.taskdevicepluginconfig[0] = par
  return True

 def plugin_receivedata(self,data):       # Watching for incoming mqtt commands
  if (len(data)>0):
#   print(data)
   self.set_value(1,str(data[0]),False)

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized:
   self.play(value)
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)
 
 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "playaudiobg":
   try:
    rname = cmdarr[1].strip()
   except:
    rname = ""
   if rname != "" and rname.lower() == self.taskname.lower():
    if len(cmdarr)>2:
     par = ""
     for i in range(2,len(cmdarr)):
      par += cmdarr[i]+","
     self.set_value(1,str(par),True)
     res = True
  return res

 def play(self,filenames): # comma separated mp3 filenames to play in order one-by-one
   if Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] != self.taskindex:
    if Settings.SoundSystem["askplugintorelease"] != None:
     try:
      Settings.SoundSystem["askplugintorelease"]() # ask to stop
     except Exception as e:
      print(e) # DEBUG
   if (Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] == self.taskindex) or (self.playing):
    self.stop()
   if Settings.SoundSystem["inuse"]: # endless loop? condition to exit?
    time.sleep(0.2)
   if Settings.SoundSystem["inuse"]==False:
    if filenames == "":
     self.stop()
     return False
    else:
     Settings.SoundSystem["inuse"] = True
     Settings.SoundSystem["usingplugintaskindex"] = self.taskindex
     Settings.SoundSystem["askplugintorelease"] = self.stop
     self.playing = True
     self.sndthread = threading.Thread(target=self.backgroundplay,args=(filenames,))
     self.sndthread.daemon = True
     self.sndthread.start()
   return self.playing

 def backgroundplay(self,commaseparatedfilenames):
  csfn = commaseparatedfilenames.split(",")
  dirname = self.taskdevicepluginconfig[0]
#  print(dirname)
#  print(csfn)
  if len(csfn)>0:
   if dirname[len(dirname)-1] != "/":
    dirname += "/"
   pygame.mixer.init()
   for fn in range(len(csfn)):
    if csfn[fn].strip()!="":
     try:
      self.uservar[0] = csfn[fn]
      pygame.mixer.music.load(str(dirname)+csfn[fn]+".mp3")
      pygame.mixer.music.play()
     except Exception as e:
      pass
     while pygame.mixer.get_init() and pygame.mixer.music.get_busy() and self.playing:
      time.sleep(0.2)
     if (self.playing==False) or (pygame.mixer.get_init()==False):
      fn = len(csfn)-1
      break
  self.stop()

 def stop(self,Optional=False):
  self.playing = False
  if Settings.SoundSystem["inuse"] and Settings.SoundSystem["usingplugintaskindex"] == self.taskindex:
   if pygame.mixer.get_init():
    if pygame.mixer.music.get_busy():
     pygame.mixer.music.stop()
    pygame.mixer.quit()
   Settings.SoundSystem["inuse"] = False
   Settings.SoundSystem["usingplugintaskindex"] = -1
   Settings.SoundSystem["askplugintorelease"] = None
  self.uservar[0] = ""

 def plugin_exit(self):
  self.stop(True)
  return True
