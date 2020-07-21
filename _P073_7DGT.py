#!/usr/bin/env python3
#############################################################################
########################## TM1637 plugin for RPIEasy ########################
#############################################################################
#
# Chips/displays supported:
#  0 - TM1637     -- 2 pins - 4 digits and colon in the middle (XX:XX)
#  1 - TM1637     -- 2 pins - 4 digits and dot on each digit (X.X.X.X.)
#
# Plugin can be setup as:
#  - Manual        -- display is manually updated sending commands
#                     "7dn,<number>"        (number can be negative or positive, even with decimal)
#                     "7dt,<temperature>"   (temperature can be negative or positive)
#                     "7dst,<hh>,<mm>"      (show manual time -not current-, no checks done on numbers validity!)
#                     "7dsd,<dd>,<mm>"      (show manual date -not current-, no checks done on numbers validity!)
#                     "7dtext,<text>"       (show free text - supported chars 0-9,a-z,A-Z," ","-","=","_","/","^")
#  - Clock-Blink     -- display is automatically updated with current time and blinking dot/lines
#  - Clock-NoBlink   -- display is automatically updated with current time and steady dot/lines
#  - Clock12-Blink   -- display is automatically updated with current time (12h clock) and blinking dot/lines
#  - Clock12-NoBlink -- display is automatically updated with current time (12h clock) and steady dot/lines
#  - Date            -- display is automatically updated with current date
#
# Generic commands:
#  - "7don"      -- turn ON the display
#  - "7doff"     -- turn OFF the display
#  - "7db,<0-15> -- set brightness to specific value between 0 and 15
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
from datetime import datetime
import tm1637 # pip3 install raspberrypi-python-tm1637

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 73
 PLUGIN_NAME = "Display - TM1637"
 PLUGIN_VALUENAME1 = "TM1637"
 P073_TM1637_4DGTCOLON =  1
 P073_TM1637_4DGTDOTS  =  2
 P073_DISP_MANUAL      =  1
 P073_DISP_CLOCK24BLNK =  2
 P073_DISP_CLOCK24     =  3
 P073_DISP_CLOCK12BLNK =  4
 P073_DISP_CLOCK12     =  5
 P073_DISP_DATE        =  6
 
 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_DUAL
  self.vtype = rpieGlobals.SENSOR_TYPE_NONE
  self.ports = 0
  self.valuecount = 0
  self.senddataoption = False
  self.timeroption = False
  self.timeroptional = False
  self.formulaoption = False
  self.device = None
  self.prevbl = 15
  self.blink = -1
  self.hide  = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.hide  = False
  if self.enabled==False or enableplugin==False:
   self.clrscr()
   return False
  if self.enabled:
   if int(self.taskdevicepin[0])>=0:
    self.initialized = False
    self.device = None
    try:
     if self.taskdevicepluginconfig[0]==self.P073_TM1637_4DGTDOTS:
      self.device = tm1637.TM1637Decimal(clk=int(self.taskdevicepin[0]), dio=int(self.taskdevicepin[1]))
     else:
      self.device = tm1637.TM1637(clk=int(self.taskdevicepin[0]), dio=int(self.taskdevicepin[1]))
     self.initialized = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"7DGT can not be initialized! "+str(e))
     self.device = None
     return False
    if self.device is None:
     self.initialized = False
  if self.enabled and self.initialized:
   self.uservar[0] = ""
   self.blink = -1
   self.p073_brightness(self.taskdevicepluginconfig[2])
   if int(self.taskdevicepluginconfig[1])>int(self.P073_DISP_MANUAL):
     self.timer1s = True
  else:
   self.timer1s = False

 def webform_load(self): # create html page for settings
   webserver.addFormNote("TM1637:  1st GPIO=CLK-Pin, 2nd GPIO=DIO-Pin")

   choice1 = self.taskdevicepluginconfig[0] # store display type
   options = ["TM1637 - 4 digit (colon)","TM1637 - 4 digit (dots)"]
   optionvalues = [self.P073_TM1637_4DGTCOLON,self.P073_TM1637_4DGTDOTS]
   webserver.addFormSelector("Display Type","p073_type",len(optionvalues),options,optionvalues,None,choice1)

   choice2 = self.taskdevicepluginconfig[1]
   options = ["Manual","Clock 24h - Blink","Clock 24h - No Blink","Clock 12h - Blink","Clock 12h - No Blink","Date"]
   optionvalues = [self.P073_DISP_MANUAL,self.P073_DISP_CLOCK24BLNK,self.P073_DISP_CLOCK24,self.P073_DISP_CLOCK12BLNK,self.P073_DISP_CLOCK12,self.P073_DISP_DATE]
   webserver.addFormSelector("Display Output","p073_output",len(optionvalues),options,optionvalues,None,choice2)

   webserver.addFormNumericBox("Brightness", "p073_brightness", self.taskdevicepluginconfig[2], 0, 15)
   return True

 def clrscr(self):
  try:
   if self.device is not None:
    self.device.show('    ')
    self.p073_brightness(0)
  except:
   pass

 def plugin_exit(self):
  self.clrscr()

 def p073_brightness(self,br):
  try:
   brn = int((int(br) / (15/7)))
   if int(br)>0 and int(brn)<1:
    brn = 1
  except:
   brn = 7
  if brn<0:
   brn=0
  elif brn>7:
   brn=7
  if self.device is not None:
   try:
    self.device.brightness(int(brn))
   except:
    pass
   if brn>0:
    self.prevbl = brn
    self.hide = False
   else:
    self.hide = True
    self.device._write_data_cmd()
    self.device._start()
    self.device._write_byte(tm1637.TM1637_CMD3) # OFF
    self.device._stop()

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p073_type",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[0] = int(par)
   par = webserver.arg("p073_output",params)
   if par == "":
    par = 1
   self.taskdevicepluginconfig[1] = int(par)
   par = webserver.arg("p073_brightness",params)
   if par == "":
    par = 15
   self.taskdevicepluginconfig[2] = int(par)
   self.plugin_init()
   return True

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0].startswith("7d") and self.device is not None:
   if cmdarr[0] == "7don":
    self.p073_brightness(self.prevbl)
    res = True
   elif cmdarr[0] == "7doff":
    self.p073_brightness(0)
    res = True
   elif cmdarr[0] == "7db":
    try:
     self.p073_brightness(cmdarr[1])
     res = True
    except:
     res = False
   elif cmdarr[0] == "7dtext":
    try:
     self.device.show(cmdarr[1].ljust(4),False) # colon?
     res = True
    except:
     res = False
   elif cmdarr[0] == "7dn":
    try:
     self.device.show(cmdarr[1].ljust(4))
     res = True
    except Exception as e:
     print(e)
     res = False
   elif cmdarr[0] == "7dt":
    try:
     num = float(cmdarr[1])
     if num < -9:
      self.device.show('lo') # low
     elif num > 99:
      self.device.show('hi') # high
     else:
      self.device.write(self.device.encode_string(cmdarr[1].rjust(2)+str("  "))) # decimals on 4 digits?
     self.device.write([tm1637._SEGMENTS[38], tm1637._SEGMENTS[12]], 2) # degrees C
     res = True
    except Exception as e:
     print(e)
     res = False
   elif cmdarr[0] == "7dst" or cmdarr[0]=="7dsd":
    try:
     newval = cmdarr[1]+cmdarr[2]
     self.device.show(newval,True)
     res = True
    except Exception as e:
     print(e)
     res = False
  return res

 def timer_once_per_second(self):
  if self.initialized and self.enabled:
   try:
    if self.hide:
     return True # skip display if brightness is 0
   except:
    pass
   newval = ""
   try:
    if int(self.taskdevicepluginconfig[1])==int(self.P073_DISP_MANUAL):
     self.timer1s=False
     return False
    elif int(self.taskdevicepluginconfig[1])==int(self.P073_DISP_CLOCK24BLNK):
     newval = datetime.now().strftime('%H%M')
     if self.blink<1:
      self.blink=1
     else:
      self.blink=0
    elif int(self.taskdevicepluginconfig[1])==int(self.P073_DISP_CLOCK24):
     newval = datetime.now().strftime('%H%M')
    elif int(self.taskdevicepluginconfig[1])==int(self.P073_DISP_CLOCK12BLNK):
     newval = datetime.now().strftime('%I%M')
     if self.blink<1:
      self.blink=1
     else:
      self.blink=0
    elif int(self.taskdevicepluginconfig[1])==int(self.P073_DISP_CLOCK12):
     newval = datetime.now().strftime('%I%M')
    elif int(self.taskdevicepluginconfig[1])==int(self.P073_DISP_DATE):
     newval = datetime.now().strftime('%m%d')
   except:
    pass
   if (str(newval) != str(self.uservar[0])) or (self.blink>-1):
    if self.blink<1:
     self.device.show(newval,True)
    else:
     self.device.show(newval,False)
    self.uservar[0]=newval
