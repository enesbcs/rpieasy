#!/usr/bin/env python3
#############################################################################
################ MH-Z19 CO2 sensor UART plugin for RPIEasy ##################
#############################################################################
#
# Based on Takeyuki Ueda's MH-Z19 code:
#  https://github.com/UedaTakeyuki/mh-z19/blob/master/mh_z19.py
#
# Available commands:
#  mhzcalibratezero
#  mhzreset
#  mhzabcenable
#  mhzabcdisable
#  mhzmeasurementrange2000
#  mhzmeasurementrange5000
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import lib.lib_serial as rpiSerial # pyserial is needed!

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 49
 PLUGIN_NAME = "Gases - CO2 MH-Z19 (TESTING)"
 PLUGIN_VALUENAME1 = "PPM"
 PLUGIN_VALUENAME2 = "Temperature"
 PLUGIN_VALUENAME3 = "U"
 cmd_abcon = b"\xff\x01\x79\xa0\x00\x00\x00\x00\xe6"
 cmd_abcoff = b"\xff\x01\x79\x00\x00\x00\x00\x00\x86"
 cmd_zerocalib = b"\xff\x01\x87\x00\x00\x00\x00\x00\x78"
 cmd_range5000 = b"\xff\x01\x99\x00\x00\x00\x13\x88\xcb"
 cmd_range2000 = b"\xff\x01\x99\x00\x00\x00\x07\xd0\x8F"
 cmd_reset = b"\xff\x01\x8d\x00\x00\x00\x00\x00\x72"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_SER
   self.vtype = rpieGlobals.SENSOR_TYPE_TRIPLE
   self.readinprogress = 0
   self.valuecount = 3
   self.senddataoption = True
   self.timeroption = True
   self.timeroptional = False
   self.formulaoption = True
   self._nextdataservetime = 0
   self.serdev = None

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  try:
   if str(self.taskdevicepluginconfig[0])!="0" and str(self.taskdevicepluginconfig[0]).strip()!="":
    self.serdev = None
    self.initialized = False
    if self.enabled:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: Try to connect")
     self.connect()
     if self.initialized:
      if str(self.taskdevicepluginconfig[1])=="1":
       self.p049_executecmd(self.cmd_abcoff)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: ABC disabled")
      pn = self.taskdevicepluginconfig[0].split("/")
      self.ports = str(pn[-1])
    else:
     self.ports = 0
  except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = rpiSerial.serial_portlist()
  webserver.addFormNote("For RPI use 'raspi-config' tool: 5- Interfacing Options-P6 Serial- (Kernel logging disabled + serial port hardware enabled) before enable this plugin")
  if len(options)>0:
   webserver.addHtml("<tr><td>Serial Device:<td>")
   webserver.addSelector_Head("p049_addr",False)
   for o in range(len(options)):
    webserver.addSelector_Item(options[o],options[o],(str(options[o])==str(choice1)),False)
   webserver.addSelector_Foot()

   choice2 = self.taskdevicepluginconfig[1]
   options = ["Enabled (Normal)","Disabled"]
   optionvalues = [0,1]
   webserver.addFormSelector("Auto Base Calibration","p049_abc",len(optionvalues),options,optionvalues,None,int(choice2))
  else:
   webserver.addFormNote("No serial ports found")
  return True

 def webform_save(self,params):
  par = webserver.arg("p049_addr",params)
  self.taskdevicepluginconfig[0] = str(par)
  try: 
   abc = webserver.arg("p049_abc",params)
   self.taskdevicepluginconfig[1] = int(abc)
  except:
   self.taskdevicepluginconfig[1] = 0
  self.plugin_init()
  return True

 def connect(self):
    try:
     self.serdev = rpiSerial.SerialPort(self.taskdevicepluginconfig[0],9600,ptimeout=0.5,pbytesize=rpiSerial.EIGHTBITS,pstopbits=rpiSerial.STOPBITS_ONE)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Serial failed "+str(e))
    try:
     self.initialized = self.serdev.isopened()
    except Exception as e:
     self.initialized = False
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Open failed "+str(e))

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized and self.readinprogress==0:
   self.readinprogress = 1
   try:
    val1, val2, val3 = self.p049_read()
   except Exception as e:
    val1 = None
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MH-Z19: "+str(e))
   if val1 is not None:
    self.set_value(1,val1,False)
    self.set_value(2,val2,False)
    self.set_value(3,val3,False)
    self.plugin_senddata()
    self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

 def p049_read(self):
  res1 = None
  res2 = None
  res3 = None
  try:
   self.connect()
   c = 10
   while c>0:
      c-=1
      result=self.serdev.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=self.serdev.read(9)
      if len(s) >= 9 and s[0] == 0xff and s[1] == 0x86:
       res1 = s[2]*256 + s[3]
       res2 = s[4] - 40
       res3 = s[6]*256 + s[7]
       break
   self.serdev.close()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"MH-Z19: "+str(e))
  return res1,res2,res3

 def p049_executecmd(self,cmdbuf):
  result = 0
  try:
   self.connect()
   result=self.serdev.write(cmdbuf)
   self.serdev.close()
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MH-Z19: "+str(e))
   result = 0
  return result

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0][:3]=="mhz":
   res = True
   if cmdarr[0] == "mhzcalibratezero":
       self.p049_executecmd(self.cmd_zerocalib)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: Zero calibration starts")
   elif cmdarr[0] == "mhzreset":
       self.p049_executecmd(self.cmd_reset)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: Reset")
   elif cmdarr[0] == "mhzabcenable":
       self.p049_executecmd(self.cmd_abcon)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: ABC enabled")
   elif cmdarr[0] == "mhzabcdisable":
       self.p049_executecmd(self.cmd_abcoff)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: ABC disabled")
   elif cmdarr[0] == "mhzmeasurementrange2000":
       self.p049_executecmd(self.cmd_range2000)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: Range is now 2000")
   elif cmdarr[0] == "mhzmeasurementrange5000":
       self.p049_executecmd(self.cmd_range5000)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MH-Z19: Range is now 5000")
  return res
