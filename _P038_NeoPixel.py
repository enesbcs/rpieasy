#!/usr/bin/env python3
#############################################################################
###################### Neopixel plugin for RPIEasy ##########################
#############################################################################
#
# Based on rpi_ws281x.
#
# Available commands:
#  NeoPixel,<led nr>,<red 0-255>,<green 0-255>,<blue 0-255>,<brightness 0-255>
#  NeoPixelAll,<red 0-255>,<green 0-255>,<blue 0-255>,<brightness 0-255>
#  NeoPixelLine,<start led nr>,<stop led nr>,<red 0-255>,<green 0-255>,<blue 0-255>,<brightness 0-255>
#
#    *Brightness is optional, default=255 or the one that setted at plugin settings
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import Settings
import webserver
from rpi_ws281x import *

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 38
 PLUGIN_NAME = "Output - NeoPixel Basic"
 PLUGIN_VALUENAME1 = ""

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY # default pin selector is not good for this!
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = False
  self.timeroptional = False
  self.led = None
  self.pixelnum = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if enableplugin == False or self.enabled == False:
    self.clearall()
  self.initialized = False
  if int(self.taskdevicepin[0])>=0 and self.enabled:
   self.pixelnum = int(self.taskdevicepluginconfig[0])
   wchannel = -1
   if int(self.taskdevicepin[0]) in [12,18]:
    wchannel = 0
   elif int(self.taskdevicepin[0]) in [13,19]:
    wchannel = 1
   if wchannel >= 0:
    try:
     self.led = PixelStrip(num=self.pixelnum, pin=int(self.taskdevicepin[0]),channel=wchannel,brightness=int(self.taskdevicepluginconfig[1]))
     self.led.begin() # init library
     self.clearall()
     self.initialized = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Invalid pin! "+str(self.taskdevicepin[0]))
   if self.initialized: # check pin modes
    self.ports = str("PWM"+str(wchannel))
    if len(Settings.Pinout)>0:
     for x in range(len(Settings.Pinout)):
      if Settings.Pinout[x]["canchange"]>0 and (self.ports in Settings.Pinout[x]["name"][0]):
       if str(Settings.Pinout[x]["BCM"])==str(self.taskdevicepin[0]): # own entry
         Settings.Pinout[x]["startupstate"] = 9 # special
       elif Settings.Pinout[x]["startupstate"] in [7,9]:
         Settings.Pinout[x]["startupstate"] = -1 # revert to unused
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PWM"+str(wchannel)+" channel already in use! Forget it!")
  else:
   self.led = None
   self.pixelnum = 0
   self.ports = 0

 def webform_load(self): # create html page for settings
  choice = self.taskdevicepin[0]
  webserver.addRowLabel("GPIO")
  webserver.addSelector_Head("p038_pin",False)
  if len(Settings.Pinout)>0:
    webserver.addSelector_Item(Settings.Pinout[0]["name"][0],-1,(str(choice)==-1),False,"")
  for x in range(len(Settings.Pinout)):
   if Settings.Pinout[x]["altfunc"]==0 and Settings.Pinout[x]["canchange"]>0:
    oname = Settings.Pinout[x]["name"][0]
    if "PWM" in oname:
     if Settings.Pinout[x]["canchange"]==1:
      onum=0
      try:
       onum = int(Settings.Pinout[x]["startupstate"])
       if onum<1:
        onum=0
      except:
       pass
      oname += " ("+Settings.PinStates[onum]+")"
     webserver.addSelector_Item(oname,Settings.Pinout[x]["BCM"],(str(choice)==str(Settings.Pinout[x]["BCM"])),False,"")
  webserver.addSelector_Foot()
  webserver.addFormNote("Only PWM-able pins can be used! WARNING: internal audio, I2S and other PWM functions might interfere with NeoPixel, so <a href='pinout'>disable them at the Hardware page</a>")
  webserver.addFormNumericBox("Led Count","p038_leds",self.taskdevicepluginconfig[0],1,2700)
  webserver.addFormNumericBox("Initial brightness","p038_bright",self.taskdevicepluginconfig[1],0,255)
  return True

 def webform_save(self,params): # process settings post reply
   changed = False
   try:
    par = webserver.arg("p038_pin",params)
    if par == "":
     par = -1
   except:
    par = -1
   if str(self.taskdevicepin[0]) != str(par):
    changed = True
    self.taskdevicepin[0] = int(par)

   par = webserver.arg("p038_leds",params)
   if par == "":
    par = 1
   if str(self.taskdevicepluginconfig[0]) != str(par):
    changed = True
    self.taskdevicepluginconfig[0] = int(par)

   par = webserver.arg("p038_bright",params)
   if par == "":
    par = 255
   if str(self.taskdevicepluginconfig[1]) != str(par):
    changed = True
    self.taskdevicepluginconfig[1] = int(par)
   if changed:
    self.plugin_init()
   return True

 def clearall(self):
  try:
    if self.led is not None:
     for l in range(self.pixelnum):
      self.led.setPixelColor(0, Color(0,0,0))
     self.led.show()
  except:
    pass

 def __del__(self):
  self.clearall()

 def plugin_write(self,cmd):
  res = False
  if self.initialized == False:
   return res
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "neopixel":
   pin = -1
   col = 0
   br  = -1
   try:
    pin = int(cmdarr[1].strip())
   except:
    pin = -1
   try:
    r = int(cmdarr[2].strip())
    g = int(cmdarr[3].strip())
    b = int(cmdarr[4].strip())
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
    r = 0
    g = 0
    b = 0
   try:
    br = int(cmdarr[5].strip())
   except:
    br = -1
   if pin>0 and self.pixelnum>=pin:
    pin = pin-1  # pixel number is 0 based
    col = Color(r,g,b)
    try:
     if br>-1:
      self.led.setBrightness(br)
     self.led.setPixelColor(pin,col)
     self.led.show()
     res = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
     res = False
    if res:
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"NeoPixel "+str(pin+1)+" set to ("+str(r)+","+str(g)+","+str(b)+")")
  elif cmdarr[0]=="neopixelall":
   col = 0
   br  = -1
   try:
    r = int(cmdarr[1].strip())
    g = int(cmdarr[2].strip())
    b = int(cmdarr[3].strip())
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
    r = 0
    g = 0
    b = 0
   try:
    br = int(cmdarr[4].strip())
   except:
    br = -1

   col = Color(r,g,b)
   try:
     if br>-1:
      self.led.setBrightness(br)
     for p in range(self.pixelnum):
      self.led.setPixelColor(p,col)
     self.led.show()
     res = True
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
     res = False
   if res:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"All NeoPixel set to ("+str(r)+","+str(g)+","+str(b)+")")
  elif cmdarr[0]=="neopixelline":
   col = 0
   br  = -1
   pin1 = -1
   pin2 = -1
   try:
    pin1 = int(cmdarr[1].strip())-1
   except:
    pin1 = 0
   try:
    pin2 = int(cmdarr[2].strip())-1
   except:
    pin2 = self.pixelnum
   if pin2>=pin1:
    pin2=pin1+1
   if pin2>self.pixelnum:
    pin2=self.pixelnum
   try:
    r = int(cmdarr[3].strip())
    g = int(cmdarr[4].strip())
    b = int(cmdarr[5].strip())
   except:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
    r = 0
    g = 0
    b = 0
   try:
    br = int(cmdarr[6].strip())
   except:
    br = -1
   col = Color(r,g,b)
   try:
     if br>-1:
      self.led.setBrightness(br)
     for p in range(pin1,pin2+1):
      self.led.setPixelColor(p,col)
     self.led.show()
     res = True
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
     res = False
   if res:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"NeoPixel "+str(pin1+1)+"-"+str(pin2+1)+" set to ("+str(r)+","+str(g)+","+str(b)+")")
  return res
