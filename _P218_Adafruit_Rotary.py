#!/usr/bin/env python3
#############################################################################
############## Adafruit I2C Rotary encoder plugin for RPIEasy ###############
#############################################################################
#
# Adafruit I2C Stemma QT Rotary Encoder Breakout with NeoPixel - STEMMA QT / Qwiic
# 
# Needs an I2C connection enabled and an INT GPIO connected to RPI
#
# Available commands (for onboard neopixel):
#
#  RotaryPixel,<taskname>,<red 0-255>,<green 0-255>,<blue 0-255>,<brightness 0-100>
#
#         *Brighttness is optional, default=100
#
# Based on:
#  https://github.com/adafruit/Adafruit_CircuitPython_seesaw
#
# Copyright (C) 2024 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import gpios
import Settings
import lib.lib_twowire as rpiwire
import lib.seesaw.lib_seesaw as seesaw

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 218
 PLUGIN_NAME = "Input - Adafruit I2C Rotary Encoder"
 PLUGIN_VALUENAME1 = "Counter"
 PLUGIN_VALUENAME2 = "Button"
 PIN_BUTTON = 24
 PIN_RGB = 6

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_DUAL
  self.valuecount = 2
  self.ports = 0
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.inverselogicoption = False
  self.recdataoption = False
  self.timer100ms = False
  self.sea = None
  self.pixel = None
  self.readinprogress = 0
  self.formulaoption = True
  self.initialized = False
  self.interruptval = -1

 def plugin_exit(self):
  if self.enabled:
   if self.timer100ms==False:
    try:
     gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
    except:
     pass
   try:
    if self.sea is not None:
       self.sea.disable_encoder_interrupt()
       self.sea.set_GPIO_interrupts((1<<self.PIN_BUTTON),False) #disable button interrupt
   except:
    pass
  return True

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.decimals[1]=0
  self.readinprogress = 0
  self.interruptval = -1
  self.timer100ms = False
  self.initialized = False
  if self.enabled:
   if int(self.taskdevicepin[0])>=0:
    try:
     gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.BOTH,self.p218_handler)
    except Exception as e:
     self.timer100ms = True
   try:
     i2cl = self.i2c
   except:
     i2cl = -1
   try:
    i2cport = gpios.HWPorts.geti2clist()
    if i2cl==-1:
      i2cl = int(i2cport[0])
   except:
    i2cport = []
   if len(i2cport)>0 and i2cl>-1:
     try:
      i2ca = int(self.taskdevicepluginconfig[0])
     except:
      i2ca = 0
     if i2ca>0:
      try:
       _i2bus   = rpiwire.request_i2c_device(int(i2cl),i2ca)
       self.sea = seesaw.Seesaw(_i2bus)
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Rotary I2C device requesting failed: "+str(e))
       self.initialized = False
       self.sea = None
     else:
       self.sea = None
     if self.sea is not None:
       try:
        if self.sea.encbase and self.sea.intbase: #enable encoder interrupt
           self.sea.enable_encoder_interrupt()
           self.initialized = True
           misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Adafruit I2C rotary initialized")
        if self.sea.gpiobase:
           self.sea.pin_mode(self.PIN_BUTTON, self.sea.INPUT_PULLUP) #set rotary button as pullup
           if self.sea.intbase:
              self.sea.set_GPIO_interrupts((1<<self.PIN_BUTTON),True) #enable button interrupt
        if self.sea.neopixbase:
          try:
           self.pixel = seesaw.Neopixel(self.sea,self.PIN_RGB,1) #init onboard Neopixel
          except:
           self.pixel = None
        else:
           self.pixel = None
       except Exception as e:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Adafruit I2C rotary init error "+str(e))
         self.initialized = False

   try:
    if float(self.uservar[0])<int(self.taskdevicepluginconfig[2]): # minvalue check
     self.set_value(1,self.taskdevicepluginconfig[2],False)
    if float(self.uservar[0])>int(self.taskdevicepluginconfig[3]): # maxvalue check
     self.set_value(1,self.taskdevicepluginconfig[3],False)
   except:
     self.set_value(1,self.taskdevicepluginconfig[2],False)
   if self.enabled and self.sea is not None and self.sea.encbase:
           cpos = int( float(self.uservar[0]) / int(self.taskdevicepluginconfig[1]))
           self.sea.set_encoder_position(cpos) #sync stored init position

 def webform_load(self): # create html page for settings
  webserver.addFormPinSelect("Rotary interrupt pin","taskdevicepin0",self.taskdevicepin[0])
  webserver.addFormNote("Add one RPI INPUT pin to handle input changes immediately")
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x36","0x37","0x38","0x39","0x3A","0x3B","0x3C","0x3D"]
  optionvalues = [0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D]
  webserver.addFormSelector("I2C address","p218_addr",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")

  choice1 = int(float(self.taskdevicepluginconfig[1]))
  options = ["1","2","3","4"]
  optionvalues = [1,2,3,4]
  webserver.addFormSelector("Step","p218_step",len(options),options,optionvalues,None,choice1)
  try:
   minv = int(self.taskdevicepluginconfig[2])
  except:
   minv = 0
  webserver.addFormNumericBox("Limit min.","p218_min",minv,-65535,65535)
  try:
   maxv = int(self.taskdevicepluginconfig[3])
  except:
   maxv = 100
  if minv>=maxv:
   maxv = minv+1
  webserver.addFormNumericBox("Limit max.","p218_max",maxv,-65535,65535)
  return True

 def webform_save(self,params): # process settings post reply
   p1 = self.taskdevicepin[0]
   p2 = self.taskdevicepluginconfig[0]
   par = webserver.arg("p218_addr",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
   except:
    self.taskdevicepluginconfig[0] = 0
   try:
    self.taskdevicepin[0]=int(webserver.arg("taskdevicepin0",params))
   except:
    self.taskdevicepin[0]=-1

   try:
    self.taskdevicepluginconfig[1] = int(webserver.arg("p218_step",params))
   except:
    self.taskdevicepluginconfig[1] = 1
   try:
    self.taskdevicepluginconfig[2] = int(webserver.arg("p218_min",params))
   except:
    self.taskdevicepluginconfig[2] = 0
   par = webserver.arg("p218_max",params)
   if par == "":
    par = 100
   if int(self.taskdevicepluginconfig[2])>=int(par):
    par = int(self.taskdevicepluginconfig[2])+1
   try:
    self.taskdevicepluginconfig[3] = int(par)
   except:
    self.taskdevicepluginconfig[3] = 100

   if int(p1)!=int(self.taskdevicepin[0]) or int(p2)!=int(self.taskdevicepluginconfig[0]):
    self.plugin_init()

   return True

 def plugin_read(self):
  result = False
  if self.initialized and self.enabled and self.readinprogress==0:
    self.readinprogress = 1
    try:
     bstat = (1-self.sea.digital_read(self.PIN_BUTTON)) #pullup button
    except Exception as e:
     print(e)
     bstat = 0
    try:
     rpos = self.sea.encoder_position()
    except Exception as e:
     print(e)
     return False #retry?
    try:
     cpos = rpos * int(self.taskdevicepluginconfig[1])
    except:
     cpos = rpos
    if cpos < int(self.taskdevicepluginconfig[2]): #enforce min limit
       cpos = int(self.taskdevicepluginconfig[2])
    if cpos > int(self.taskdevicepluginconfig[3]): #enforce max limit
       cpos = int(self.taskdevicepluginconfig[3])
    self.set_value(1,cpos,True)
    if rpos != int(cpos / int(self.taskdevicepluginconfig[1])): #sync i2c device with logical position
       self.sea.set_encoder_position(int(cpos / int(self.taskdevicepluginconfig[1])))
    self.set_value(2,bstat,True)
    self._lastdataservetime = rpieTime.millis()
    self.readinprogress = 0
    result = True
  return result

 def timer_ten_per_second(self):
  if self.initialized and self.enabled:
     try:
      inval = gpios.HWPorts.input(int(self.taskdevicepin[0]))
     except:
      inval = -1
     if int(inval) != int(self.interruptval): #read state if interrupt pin changed
         self.p218_handler(0)
     self.interruptval = inval
     return self.timer100ms

 def p218_handler(self,channel):
     tnow = rpieTime.millis()
     self.plugin_read() #read state if interrupt called
     for t in range(0,len(Settings.Tasks)):
      if (Settings.Tasks[t] and (type(Settings.Tasks[t]) is not bool)):
         if (Settings.Tasks[t].enabled and Settings.Tasks[t].taskindex != self.taskindex and Settings.Tasks[t].pluginid == self.pluginid):
            if int(Settings.Tasks[t].taskdevicepin[0]) == int(self.taskdevicepin[0]): #make sure if every rotary is notified on the same interrupt pin
             if tnow - Settings.Tasks[t]._lastdataservetime >= 100: #updated long time ago
                Settings.Tasks[t].plugin_read()

 def plugin_write(self,cmd):
  res = False
  if self.initialized == False:
   return res
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "rotarypixel":
   if cmdarr[1].strip().lower() != self.taskname:
      return False # not for this device
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
   try:
    if self.pixel is not None:
      if br>100:
         br=100
      br = float(br/100)
      if br > -1:
       self.pixel.brightness = br
      self.pixel.fill( (r,g,b) )
      res = True
   except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Neopixel error "+str(e))
     res = False
   if res:
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"NeoPixel set to ("+str(r)+","+str(g)+","+str(b)+")")
  return res
