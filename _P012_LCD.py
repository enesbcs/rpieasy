#!/usr/bin/env python3
#############################################################################
########################## LCD plugin for RPIEasy ###########################
#############################################################################
#
# Available commands:
#  LCDCMD,<value>           - value can be: on, off, clear
#  LCDCMD,clearline,<row>   - clears selected <row>
#  LCD,<row>,<col>,<text>   - write text message to LCD screen at the requested position
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import commands
from RPLCD.i2c import CharLCD

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 12
 PLUGIN_NAME = "Display - LCD2004 I2C"
 PLUGIN_VALUENAME1 = "LCD"
 P12_Nlines = 4

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
  self.linelens = [0,0,0,0]

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  if self.enabled==False or enableplugin==False:
   self.__del__()
   return False
  if self.enabled:
   if int(self.taskdevicepin[0])>=0:
    try:
     gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
    except:
     pass
    try:
     gpios.HWPorts.add_event_detect(int(self.taskdevicepin[0]),gpios.BOTH,self.p012_handler)
     self.timer100ms = False
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Event can not be added, register backup timer "+str(e))
     self.timer100ms = True
   else:
     self.timer100ms = False
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
    self.device = None
    try:
     if "x" in str(self.taskdevicepluginconfig[2]):
      resstr = str(self.taskdevicepluginconfig[2]).split('x')
      self.width = int(resstr[0])
      self.height = int(resstr[1])
     else:
      self.width  = None
      self.height = None
    except:
     self.width  = None
     self.height = None
    if str(self.taskdevicepluginconfig[0]) != "0" and str(self.taskdevicepluginconfig[0]).strip() != "" and self.taskdevicepluginconfig[1]>0 and self.height is not None:
     try:
       self.device = CharLCD(i2c_expander=str(self.taskdevicepluginconfig[0]), address=int(self.taskdevicepluginconfig[1]), port=i2cport,
              cols=self.width, rows=self.height, auto_linebreaks=(str(self.taskdevicepluginconfig[3])=="1"), backlight_enabled=(str(self.taskdevicepluginconfig[4])=="1"))
       self.uservar[0] = 1
       self.initialized = True
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LCD can not be initialized! "+str(e))
      self.device = None
      return False
    if self.device is not None:
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    else:
     self.initialized = False
   else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LCD I2C error! ")

 def webform_load(self): # create html page for settings
  choice1 = str(self.taskdevicepluginconfig[0]) # store display type
  options = ["PCF8574","MCP23008","MCP23017"]
  webserver.addHtml("<tr><td>I2C chip type:<td>")
  webserver.addSelector_Head("p012_type",True)
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice1==options[d]),False)
  webserver.addSelector_Foot()

  choice2 = int(float(self.taskdevicepluginconfig[1])) # store i2c address
  optionvalues = []
  for i in range(0x20,0x28):
   optionvalues.append(i)
  for i in range(0x38,0x40):
   optionvalues.append(i)
  options = []
  for i in range(len(optionvalues)):
   options.append(str(hex(optionvalues[i])))
  webserver.addFormSelector("Address","p012_adr",len(options),options,optionvalues,None,choice2)
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")

  choice3 = self.taskdevicepluginconfig[2] # store resolution
  webserver.addHtml("<tr><td>Resolution:<td>")
  webserver.addSelector_Head("p012_res",False)
  options = ["16x2","20x4"]
  for d in range(len(options)):
   webserver.addSelector_Item(options[d],options[d],(choice3==options[d]),False)
  webserver.addSelector_Foot()

  choice4 = int(float(self.taskdevicepluginconfig[3])) # store linewrap state
  options =      ["Auto","None"]
  optionvalues = [1,0]
  webserver.addFormSelector("Linebreak","p012_break",len(optionvalues),options,optionvalues,None,choice4)

  choice5 = int(float(self.taskdevicepluginconfig[4])) # store backlight state
  options =      ["Enabled","Disabled"]
  optionvalues = [1,0]
  webserver.addFormSelector("Backlight","p012_blight",len(optionvalues),options,optionvalues,None,choice5)

  if "x2" in str(self.taskdevicepluginconfig[2]):
   lc = 2
  else:
   lc = 4
  for l in range(lc):
   try:
    linestr = self.lines[l]
   except:
    linestr = ""
   webserver.addFormTextBox("Line"+str(l+1),"p012_template"+str(l),linestr,128)
  webserver.addFormPinSelect("Display button","taskdevicepin0",self.taskdevicepin[0])
  return True

 def __del__(self):
  try:
   if self.device is not None:
    self.device.clear()
    self.device._set_backlight_enabled(False)
  except:
   pass
  if self.enabled and self.timer100ms==False and (self.taskdevicepin[0]>-1):
   try:
    gpios.HWPorts.remove_event_detect(int(self.taskdevicepin[0]))
   except:
    pass

 def plugin_exit(self):
  self.__del__()

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p012_type",params)
   if par == "":
    par = "PCF8574"
   self.taskdevicepluginconfig[0] = str(par)

   par = webserver.arg("p012_adr",params)
   if par == "":
    par = 0x27
   self.taskdevicepluginconfig[1] = int(par)

   par = webserver.arg("p012_res",params)
   self.taskdevicepluginconfig[2] = str(par)

   par = webserver.arg("p012_break",params)
   self.taskdevicepluginconfig[3] = str(par)

   par = webserver.arg("p012_blight",params)
   self.taskdevicepluginconfig[4] = str(par)

   for l in range(self.P12_Nlines):
    linestr = webserver.arg("p012_template"+str(l),params).strip()
    try:
      self.lines[l]=linestr
    except:
      self.lines.append(linestr)
   try:
    self.taskdevicepin[0]=int(webserver.arg("taskdevicepin0",params))
   except:
    self.taskdevicepin[0]=-1
   self.plugin_init()
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  if self.initialized and self.enabled and self.device and self.height:
     try:
       for l in range(int(self.height)):
        resstr = ""
        try:
         linestr=str(self.lines[l])
         resstr=self.lcdparse(linestr)
        except Exception as e:
         resstr=""
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LCD parse error: "+str(e))
        if resstr != "":
         if self.linelens[l]>len(resstr):
          clrstr = ""
          clrstr += ' ' * self.linelens[l]
          self.device.cursor_pos = (l, 0)
          self.device.write_string(clrstr)
         self.device.cursor_pos = (l, 0) # (row, col)
         self.device.write_string(resstr)
         self.linelens[l] = len(resstr)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LCD write error! "+str(e))
     self._lastdataservetime = rpieTime.millis()
  return True

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "lcdcmd":
   try:
    cmd = cmdarr[1].strip()
   except:
    cmd = ""
   try:
    if self.device is not None:
     if cmd == "on":
      self.device._set_backlight_enabled(True)
      res = True
     elif cmd == "off":
      self.device._set_backlight_enabled(False)
      res = True
     elif cmd == "clear":
      self.device.clear()
      res = True
     elif cmd == "clearline":
      try:
       l = int(cmdarr[2].strip())
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
       return False
      if self.device is not None and self.height is not None:
        if l>0:
         l-=1
        clrstr = ""
        clrstr  += ' ' * self.width
        self.device.cursor_pos = (l, 0)
        self.device.write_string(clrstr)
      res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LCD command error! "+str(e))
    res = False
  elif cmdarr[0] == "lcd":
   sepp = len(cmdarr[0])+len(cmdarr[1])+len(cmdarr[2])+1
   sepp = cmd.find(',',sepp)
   try:
    y = int(cmdarr[1].strip())
    x = int(cmdarr[2].strip())
    text = cmd[sepp+1:]
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Parameter error: "+str(e))
    return False
   if x>0 and y>0:
    x -= 1
    y -= 1
   try:
    if self.device is not None:
      self.device.cursor_pos = (y, x)
      resstr = self.lcdparse(text)
      self.device.write_string(resstr)
      res = True
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"LCD command error! "+str(e))
    res = False
  return res

 def lcdparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
      return resstr

 def p012_handler(self,channel):
  self.timer_ten_per_second()

 def timer_ten_per_second(self):
  if self.initialized and self.enabled:
   val = gpios.HWPorts.input(int(self.taskdevicepin[0]))
   if int(val) != int(float(self.uservar[0])):
    self.uservar[0] = int(val)
    if int(val)==0:
     if self.device._get_backlight_enabled():
       self.device._set_backlight_enabled(False)
     else:
      self.device._set_backlight_enabled(True)
