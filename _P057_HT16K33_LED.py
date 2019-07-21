#!/usr/bin/env python3
#############################################################################
##################### HT16K33 LED plugin for RPIEasy ########################
#############################################################################
#
# ESPEasy Plugin to control a 16x8 LED matrix with chip HT16K33
#
# List of commands:
#  M,<param>,<param>,<param>, ...    with decimal values
#  MNUM,<param>,<param>,<param>, ...    with decimal values for 7-segment displays
#  MBR,<0-15>    set display brightness, between 0 and 15
#
# List of M* params:
#  <value>
#    Writes a decimal values to actual segment starting with 0
#  <seg>=<value>
#    Writes a decimal values to given segment (0...7)
# "CLEAR"
#    Set all LEDs to 0.
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import rpieGlobals
import rpieTime
import time
import misc
import gpios
import webserver
import lib.HT16K33.Adafruit_8x8 as HT16K33
import lib.HT16K33.Adafruit_7Segment as HT167S

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 57
 PLUGIN_NAME = "Display - HT16K33 LED (EXPERIMENTAL)"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = False
  self.inverselogicoption = False
  self.recdataoption = False
  self.ht16 = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.initialized = False
  self.timer100ms = False
  if self.enabled:
   i2cport = -1
   try:
    for i in range(0,2):
     if gpios.HWPorts.is_i2c_usable(i) and gpios.HWPorts.is_i2c_enabled(i):
      i2cport = i
      break
   except:
    i2cport = -1
   if i2cport>-1:
     try:
      i2ca = int(self.taskdevicepluginconfig[0])
     except:
      i2ca = 0
     if i2ca>0:
      try:
       if int(self.taskdevicepluginconfig[1])==1:
        self.ht16 = HT167S.SevenSegment(address=int(i2ca),i2cbusnum=i2cport)
       else:
        self.ht16 = HT16K33.EightByEight(address=int(i2ca),i2cbusnum=i2cport)
       self.timer100ms = True
       self.initialized = True
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 device requesting failed: "+str(e))
       self.ht16 = None

 def webform_load(self):
  choice1 = int(float(self.taskdevicepluginconfig[0])) # store i2c address
  optionvalues = []
  for i in range(0x70, 0x78):
   optionvalues.append(i)
  options = []
  for i in range(len(optionvalues)):
   options.append(str(hex(optionvalues[i])))
  webserver.addFormSelector("Address","p057_adr",len(options),options,optionvalues,None,choice1)
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")

  choice2 = int(float(self.taskdevicepluginconfig[1]))
  options = ["Direct 8-16 rows","7 segment"]
  optionvalues = [0,1]
  webserver.addFormSelector("Display type","p057_type",len(options),options,optionvalues,None,choice2)

  return True

 def webform_save(self,params):
   cha = False

   par = webserver.arg("p057_adr",params)
   if par == "":
    par = 0x70
   if self.taskdevicepluginconfig[0] != int(par):
    cha = True
   self.taskdevicepluginconfig[0] = int(par)

   par = webserver.arg("p057_type",params)
   if par == "":
    par = 0x70
   if self.taskdevicepluginconfig[1] != int(par):
    cha = True
   self.taskdevicepluginconfig[1] = int(par)

   if cha:
    self.plugin_init()
   return True

 def plugin_write(self,cmd):
  res = False
  if self.ht16 is None:
   return res
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()

  if cmdarr[0] == "mbr":
   res = True
   try:
      val = int(cmdarr[1].strip())
   except:
      val = -1
   if val>-1 and val<16:
    try:
     self.ht16.disp.setBrightness(val)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))

  elif cmdarr[0] == "m":
   for c in range(len(cmdarr)):
    if "=" in cmdarr[c]: # seg=value
     res = True
     lv = cmdarr[c].split("=")
     try:
      c0 = int(lv[0].strip())
      r0 = int(lv[1].strip())
     except:
      c0 = -1
      r0 = -1
     if c0>=0 and c0<16 and r0>=0:
      try:
       if int(self.taskdevicepluginconfig[1])==1:
        self.ht16.writeDigitRaw(c0,r0)
       else:
        self.ht16.writeRowRaw(c0,r0)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))
    elif cmdarr[c].strip().lower()=="clear":
     res = True
     try:
      if int(self.taskdevicepluginconfig[1])==1:
       self.ht16.disp.clear()
      else:
       self.ht16.clear()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))
    else:
     try:
      val = int(cmdarr[c].strip())
      res = True
     except:
      val = -1
     if val>-1 and c<16:
      try:
       if int(self.taskdevicepluginconfig[1])==1:
        self.ht16.writeDigitRaw(c-1,val)
       else:
        self.ht16.writeRowRaw(c-1,val)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))

  elif cmdarr[0] == "mnum":
   if int(self.taskdevicepluginconfig[1])!=1:
    return False
   for c in range(len(cmdarr)):
    if "=" in cmdarr[c]: # seg=value
     res = True
     lv = cmdarr[c].split("=")
     try:
      c0 = int(lv[0].strip())
      r0 = int(lv[1].strip())
     except:
      c0 = -1
      r0 = -1
     if c0>=0 and c0<16 and r0>=0:
      try:
       self.ht16.writeDigit(c0,r0)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))
    elif cmdarr[c].strip().lower()=="clear":
     res = True
     try:
      self.ht16.disp.clear()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))
    else:
     try:
      val = int(cmdarr[c].strip())
      res = True
     except:
      val = -1
     if val>-1 and c<16:
      try:
        self.ht16.writeDigit(c-1,val)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"HT16K33 error: "+str(e))

  return res
