#!/usr/bin/env python3
#############################################################################
########################## OLED plugin for RPIEasy ##########################
#############################################################################
#
# Available commands:
#  OLEDCMD,value          - value can be: on, off, clear
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import commands
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from PIL import ImageFont

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 23
 PLUGIN_NAME = "Display - Simple OLED (TESTING)"
 PLUGIN_VALUENAME1 = "OLED"
 P23_Nlines = 8

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.ports = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = False
  self.device = None
  self.width  = None
  self.height = None
  self.lines  = []
  self.ufont  = None
  self.lineheight = 11

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
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
    if self.interval>2:
      nextr = self.interval-2
    else:
      nextr = self.interval

    self.initialized = False
    serialdev = None
    self.taskdevicepluginconfig[1] = int(float(self.taskdevicepluginconfig[1]))
    if self.taskdevicepluginconfig[1] != 0: # i2c address
     serialdev = i2c(port=i2cport, address=self.taskdevicepluginconfig[1])
    else:
     return self.initialized
    self.device = None
    try:
     if "x" in str(self.taskdevicepluginconfig[3]):
      resstr = str(self.taskdevicepluginconfig[3]).split()
      self.width = int(resstr[0])
      self.width = int(resstr[1])
     else:
      self.width  = None
      self.height = None
    except:
     self.width  = None
     self.height = None

    if str(self.taskdevicepluginconfig[0]) != "0" and str(self.taskdevicepluginconfig[0]).strip() != "": # display type
     try:
      if str(self.taskdevicepluginconfig[0])=="ssd1306":
       from luma.oled.device import ssd1306
       if self.height is None:
        self.device = ssd1306(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1306(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="sh1106":
       from luma.oled.device import sh1106
       if self.height is None:
        self.device = sh1106(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = sh1106(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1309":
       from luma.oled.device import ssd1309
       if self.height is None:
        self.device = ssd1309(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1309(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1331":
       from luma.oled.device import ssd1331
       if self.height is None:
        self.device = ssd1331(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1331(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1351":
       from luma.oled.device import ssd1351
       if self.height is None:
        self.device = ssd1351(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1351(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1322":
       from luma.oled.device import ssd1322
       if self.height is None:
        self.device = ssd1322(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1322(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1325":
       from luma.oled.device import ssd1325
       if self.height is None:
        self.device = ssd1325(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1325(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
      elif str(self.taskdevicepluginconfig[0])=="ssd1327":
       from luma.oled.device import ssd1327
       if self.height is None:
        self.device = ssd1327(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])))
       else:
        self.device = ssd1327(serialdev, rotate=int(float(self.taskdevicepluginconfig[2])), width=self.width, height=self.height)
       self.initialized = True
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"OLED can not be initialized! "+str(e))
      self.enabled = False
      self.device = None
      return False
    if self.device is not None:
     try:
      lc = int(self.taskdevicepluginconfig[4])
     except:
      lc = self.P23_Nlines
     if lc < 1:
      lc = self.P23_Nlines
     lineheight = int(self.device.height / lc)+2
     self.ufont=ImageFont.truetype('img/UbuntuMono-R.ttf', lineheight)
     try:
      self.device.show()
     except:
      pass
     with canvas(self.device) as draw:
      try:
       self.lineheight = draw.textsize("NS",self.ufont)[1]
      except:
       self.lineheight = 11
#     print(lineheight,lheight)
    else:
     self.initialized = False

 def webform_load(self): # create html page for settings
  choice1 = str(self.taskdevicepluginconfig[0]) # store display type
  import luma.oled.device
  options = luma.oled.device.__all__
  webserver.addHtml("<tr><td>Display type:<td>")
  webserver.addSelector_Head("p023_type",True)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice1==options[d]),False)
  webserver.addSelector_Foot()
  choice2 = int(float(self.taskdevicepluginconfig[1])) # store i2c address
  options = ["0x3c","0x3d"]
  optionvalues = [0x3c,0x3d]
  webserver.addFormSelector("Address","p023_adr",len(options),options,optionvalues,None,choice2)
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  choice3 = int(float(self.taskdevicepluginconfig[2])) # store rotation state
  options =      ["Normal","Rotate by 90","Rotate by 180","Rotate by 270"]
  optionvalues = [0,1,2,3]
  webserver.addFormSelector("Mode","p023_rotate",len(optionvalues),options,optionvalues,None,choice3)
  options = ["Default","128x64","128x128","128x32","96x96","96x64","64x48","64x32"]
  choice4 = self.taskdevicepluginconfig[3] # store resolution
  webserver.addHtml("<tr><td>Resolution:<td>")
  webserver.addSelector_Head("p023_res",False)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice4==options[d]),False)
  webserver.addSelector_Foot()

  choice5 = int(float(self.taskdevicepluginconfig[4])) # store line count
  webserver.addHtml("<tr><td>Number of lines:<td>")
  webserver.addSelector_Head("p023_linecount",False)
  for l in range(1,self.P23_Nlines+1):
   webserver.addSelector_Item(str(l),l,(l==choice5),False)
  webserver.addSelector_Foot()
  if choice5 > 0 and choice5<9:
   lc = choice5
  else:
   lc = self.P23_Nlines
  for l in range(lc):
   try:
    linestr = self.lines[l]
   except:
    linestr = ""
   webserver.addFormTextBox("Line"+str(l),"p023_template"+str(l),linestr,128)

  return True

 def __del__(self):
  try:
   if self.device is not None:
    self.device.clear()
    self.device.hide()
  except Exception as e:
   print(e)

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p023_type",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[0] = str(par)

   par = webserver.arg("p023_adr",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[1] = int(par)

   par = webserver.arg("p023_rotate",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[2] = int(par)

   par = webserver.arg("p023_res",params)
   self.taskdevicepluginconfig[3] = str(par)

   par = webserver.arg("p023_linecount",params)
   if par == "":
    par = 8
   self.taskdevicepluginconfig[4] = int(par)

   for l in range(self.P23_Nlines):
    linestr = webserver.arg("p023_template"+str(l),params).strip()
    if linestr!="" and linestr!="0":
     try:
      self.lines[l]=linestr
     except:
      self.lines.append(linestr)
   self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  if self.initialized and self.enabled:
   with canvas(self.device) as draw:
     try:
      for l in range(int(self.taskdevicepluginconfig[4])):
        resstr = ""
        try:
         linestr=self.lines[l]
         cl, st = commands.parseruleline(linestr)
         if st=="CMD":
          resstr=cl
         else:
          resstr=linestr
        except:
         resstr=""
        draw.text( (0,(l*self.lineheight)), resstr, fill="white", font=self.ufont)
     except Exception as e:
      print(e)
     self._lastdataservetime = rpieTime.millis()
  return True

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "oledcmd":
   try:
    cmd = cmdarr[1].strip()
   except:
    cmd = ""
   try:
    if self.device is not None:
     if cmd == "on":
      self.device.show()
      res = True
     elif cmd == "off":
      self.device.hide()
      res = True
     elif cmd == "clear":
      self.device.clear()
      res = True
   except Exception as e:
    print(e) 
    res = False
  return res
