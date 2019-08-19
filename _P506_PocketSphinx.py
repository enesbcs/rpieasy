#!/usr/bin/env python3
#############################################################################
############ Pocket Sphinx speech recognition lugin for RPIEasy #############
#############################################################################
#
# PocketSphinx support through SpeechRecognition python module
#  https://pypi.org/project/SpeechRecognition/
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import speech_recognition as sr

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 506
 PLUGIN_NAME = "Input - PocketSphinx Speech Recognition (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "Text"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SND
   self.vtype = rpieGlobals.SENSOR_TYPE_TEXT
   self.readinprogress = 0
   self.valuecount = 1
   self.senddataoption = True
   self.timeroption = False
   self.timeroptional = False
   self.formulaoption = False
   self.mic   = None
   self.rprocess = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  if self.enabled:
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Init speech recognition")
   try:
    recog = sr.Recognizer()
    print("--- DEBUG MESSAGES ---")
    self.mic = sr.Microphone()
    print("--- DEBUG MESSAGES END ---")
    print("Available mics: ", self.mic.list_microphone_names())
    self.initialized = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SpeechRecognition error: "+str(e))
    self.initialized = False
   if self.initialized:
    try:
     with self.mic as source:
      recog.adjust_for_ambient_noise(source, duration=0.5)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SpeechRecognition error: "+str(e))
     self.initialized = False
   self.readinprogress = 0
   if self.initialized:
    self.rprocess = recog.listen_in_background(self.mic,self.processor)
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"SpeechRecognition start listening")
  else:
   self.plugin_exit()

 def webform_load(self):
  return True

 def webform_save(self,params):
#  par = webserver.arg("p509_addr",params)
#  self.taskdevicepluginconfig[0] = str(par)
  return True

 def processor(self,recognizer,audio):
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Speech decoding started")
  if self.readinprogress == 0:
   res = ""
   self.readinprogress = 1
   try:
    res = recognizer.recognize_sphinx(audio)
   except sr.UnknownValueError:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"SpeechRecognition: Could not understand")
   except sr.RequestError as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"SpeechRecognition error: "+str(e))
   if res != "":
    self.set_value(1,str(res),True)
   self.readinprogress = 0
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Speech decoding ended")

 def plugin_exit(self):
  try:
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"SpeechRecognition stop listening")
   self.rprocess(wait_for_stop=False)
  except:
   pass
 