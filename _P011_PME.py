#!/usr/bin/env python3
#############################################################################
################### Pro Mini Extender plugin for RPIEasy ####################
#############################################################################
#
# https://www.letscontrolit.com/wiki/index.php/ProMiniExtender
#
# If you are experiencing any slowdown, or stopping in data flow, please use this v2 sketch on PME:
#  https://github.com/enesbcs/ESPEasySlaves/blob/master/MiniProExtender/MiniProExtender.ino
#
# Available commands:
#  EXTGPIO,<pin>,<state>		 - digital GPIO output, state can be: 0/1
#  EXTPWM,<pin>,<level>			 - level can be 0-255 which is proportional to 0V to VCC
#  EXTPULSE,<pin>,<state>,<duration>	 - state can be 0/1, set gpio to <state> then after <duration> milliseconds reverses it's state
#  EXTLONGPULSE,<pin>,<state>,<duration> - state can be 0/1, set gpio to <state> then after <duration> seconds reverses it's state
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# Made with the support of happytm
# This plugin would never have been created without happytm! :)
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time
import rpiwire

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 11
 PLUGIN_NAME = "Extra IO - ProMini Extender (TESTING)"
 PLUGIN_VALUENAME1 = "Value"
 CMD_DIGITAL_WRITE = 1
 CMD_DIGITAL_READ  = 2
 CMD_ANALOG_WRITE  = 3
 CMD_ANALOG_READ   = 4
 ANALOG_DIVERSION  = 1

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.ports = 0
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self.pme = None
  self.sketch = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
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
      dport = int(self.taskdevicepluginconfig[0])
     except:
      dport = 0
     if dport == 0:
      dport = 0x3f
     self.pme = None
     try:
      self.pme = rpiwire.request_i2c_device(int(i2cport),dport)
     except Exception as e:
      self.pme = None
   if self.pme:
    try:
     if str(self.pme.i2c_bus_num) != str(i2cport):
      self.pme = None
    except Exception as e:
     self.pme = None
   if self.pme is None:
    self.enabled = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PME can not be initialized! ")
    return False
   else:
    self.sketch = self.check_sketch()
    if self.sketch==0:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Used PME sketch is outdated! Try: https://github.com/enesbcs/ESPEasySlaves/blob/master/MiniProExtender/MiniProExtender.ino")
     self.pme.setEndDelay(0.1) # increase timeout for old sketch as it is unable to handle multiple fast calls repeatedly
    else:
     self.pme.setEndDelay(0.001)
    self.initialized = True
    try:
     self.ports = str(self.taskdevicepluginconfig[2])
    except:
     self.ports = 0
    if self.interval>0:
     self.timer100ms = False # normal read
    else:
     self.uservar[0] = -1
     self.readinprogress = 0
     self.timer100ms = True  # oversampling method
#     if sketch==0:
#      if str(self.taskdevicepluginconfig[1])=="1":
#       self.timer100ms = False # oversampling will not work for analog read
  else:
   self.ports = 0
 
 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x3f","0x4f","0x5f","0x6f","0x7f"]
  optionvalues = [0x3f,0x4f,0x5f,0x6f,0x7f]
  webserver.addFormSelector("I2C address","plugin_011_addr",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>! 0x7F address is non-standard, so it may not work!")
  choice2 = self.taskdevicepluginconfig[1]
  options = ["Digital","Analog"]
  optionvalues = [0,1]
  webserver.addFormSelector("Type","plugin_011_ptype",2,options,optionvalues,None,int(choice2))
  webserver.addFormNumericBox("Port number","plugin_011_pnum",self.taskdevicepluginconfig[2],0,30)
  webserver.addFormNote("Digital ports 0-13, Analog ports 0-7 (20-27)")
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("plugin_011_addr",params)
   if par == "":
    par = 0
   self.taskdevicepluginconfig[0] = int(par)
   par = webserver.arg("plugin_011_ptype",params)
   try:
    self.taskdevicepluginconfig[1] = int(par)
   except:
    self.taskdevicepluginconfig[1] = 0
   par = webserver.arg("plugin_011_pnum",params)
   try:
    self.taskdevicepluginconfig[2] = int(par)
   except:
    self.taskdevicepluginconfig[2] = 0
   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.enabled and self.readinprogress==0:
    self.readinprogress = 1
    try:
     pt = int(self.taskdevicepluginconfig[1])
     pn = int(self.taskdevicepluginconfig[2])
     readcmd = self.create_read_buffer(pt,pn)
    except Exception as e:
     return False
    pmeid = self.pme.beginTransmission(pn,True)
    if pmeid != 0:
     try:
      self.pme.write(readcmd,pmeid)   # send read data command
      if pt==0:
       time.sleep(0.001)       # digital read is almost instantous
      else:
       time.sleep(0.01)       # analog read takes more time
      data = self.pme.read(4,pmeid) # read data
      if len(data)>3:
       if data[2] == data[3] and data[3] == 255:
        if self.sketch==0:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ProMini I2C frozen, restart it manually and consider using new sketch!")
        data = []
      self.pme.endTransmission(pmeid)
      result = 0
      if len(data)>0:
       if pt==0:
        result = int(data[0])
        if result not in [0,1]: # invalid value,digital can only be 0 or 1!
         return False
       elif len(data)>1:
        result = (data[1] << 8 | data[0]) # 0-1023
       self.set_value(1,result,True)
       self._lastdataservetime = rpieTime.millis()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.readinprogress = 0
    result = True
  return result

 def timer_ten_per_second(self):
  if self.readinprogress == 0 and self.timer100ms and self.initialized:
    self.readinprogress = 1
    try:
     pt = int(self.taskdevicepluginconfig[1])
     pn = int(self.taskdevicepluginconfig[2])
     readcmd = self.create_read_buffer(pt,pn)
    except:
     return False
    pmeid = self.pme.beginTransmission(pn,True)
    if pmeid != 0:
     try:
      self.pme.write(readcmd,pmeid)   # send read data command
      if pt==0:
       time.sleep(0.001)       # digital read is almost instantous
      else:
       time.sleep(0.01)       # analog read takes more time
      data = self.pme.read(4,pmeid) # read data
      if len(data)>3:
       if data[2] == data[3] and data[3] == 255:
        if self.sketch==0:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"ProMini I2C frozen, restart it manually and consider using new sketch!")
        data = []
      self.pme.endTransmission(pmeid)
      result = 0
      if len(data)>0:
       if pt==0:
        result = int(data[0])
        if result not in [0,1]: # invalid value,digital can only be 0 or 1!
         return False
        if float(result)!=float(self.uservar[0]):
         self.set_value(1,result,True)
       elif len(data)>1:
        result = int(data[1] << 8 | data[0]) # 0-1023
        if abs(result-float(self.uservar[0]))>self.ANALOG_DIVERSION:
         self.set_value(1,result,True)
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.readinprogress = 0
  return self.timer100ms

 def create_read_buffer(self,ptype,pnum):
   try:
    pnum = int(pnum) & 0xFF
    ptype = int(ptype)
   except:
    return bytes([])
   if ptype == 1 and pnum>19:
    pnum -= 20
   carr = []
   if ptype==0:
    carr.append(self.CMD_DIGITAL_READ) # 0 or 1
   else:
    carr.append(self.CMD_ANALOG_READ) # 0-1023
   carr.append(pnum)
   carr.append(0)
   carr.append(0)
   return bytes(carr)

 def create_write_buffer(self,ptype,pnum,value):
  # ptype 0=digital,1=analog
   try:
    pnum = int(pnum) & 0xFF
    ptype = int(ptype)
   except:
    return bytes([])
   if ptype == 1 and pnum>19:
    pnum -= 20
   carr = []
   if ptype==0:
    carr.append(self.CMD_DIGITAL_WRITE) # 0 or 1
   else:
    carr.append(self.CMD_ANALOG_WRITE)  # 0-255
   carr.append(pnum)
   carr.append((value & 0xff))
   carr.append((value >> 8))
   return bytes(carr)

 def plugin_write(self,cmd): # handle incoming commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower() # implement scanning of devices to sync taskvalues??
  if cmdarr[0] == "extgpio":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   if pin>-1 and val in [0,1]:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EXTGPIO"+str(pin)+" set to "+str(val))
    try:
     writecmd = self.create_write_buffer(0,pin,val)
     self.pme_write_retry(writecmd,pin)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EXTGPIO"+str(pin)+": "+str(e))
   res = True
  elif cmdarr[0]=="extpwm":
   pin = -1
   prop = -1
   try:
    pin = int(cmdarr[1].strip())
    prop = int(cmdarr[2].strip())
   except:
    pin = -1
    prop = -1
   if pin>-1 and prop>-1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EXTPWM"+str(pin)+": "+str(prop))
    try:
     writecmd = self.create_write_buffer(1,pin,prop)
     self.pme_write_retry(writecmd,pin)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EXTPWM"+str(pin)+": "+str(e))
   res = True
  elif cmdarr[0]=="extpulse":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   dur = 100
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 100
   if pin>-1 and val in [0,1]:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EXTGPIO"+str(pin)+": Pulse started")
    try:
     writecmd = self.create_write_buffer(0,pin,val)
     self.pme_write_retry(writecmd,pin)
     s = float(dur/1000)
     if s>self.pme.enddelay:
      s = (s-self.pme.enddelay) # endtransmission sleep
      time.sleep(s)
     writecmd = self.create_write_buffer(0,pin,(1-val))
     self.pme_write_retry(writecmd,pin)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EXTGPIO"+str(pin)+": "+str(e))
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EXTGPIO"+str(pin)+": Pulse ended")
   res = True
  elif cmdarr[0]=="extlongpulse":
   pin = -1
   val = -1
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   dur = 2
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 2
   if pin>-1 and val in [0,1]:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EXTGPIO"+str(pin)+": LongPulse started")
    try:
     writecmd = self.create_write_buffer(0,pin,val)
     self.pme_write_retry(writecmd,pin)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EXTGPIO"+str(pin)+": "+str(e))
    rarr = [pin,(1-val)]
    rpieTime.addsystemtimer(dur,self.p011_timercb,rarr)
   res = True
  return res

 def p011_timercb(self,stimerid,ioarray):
  if ioarray[0] > -1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"EXTGPIO"+str(ioarray[0])+": LongPulse ended")
    try:
     writecmd = self.create_write_buffer(0,ioarray[0],ioarray[1])
     self.pme_write_retry(writecmd,ioarray[0])
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EXTGPIO"+str(ioarray[0])+": "+str(e))

 def pme_write_retry(self,cmdbuf,pn):
   pmeid = 0
   for c in range(0,10):
     pmeid = self.pme.beginTransmission(pn)
     if pmeid != 0:
      break
     time.sleep(0.01)
   if pmeid != 0:
      self.pme.write(cmdbuf,pmeid)   # send write data command
      self.pme.endTransmission(pmeid)

 def check_sketch(self):
   sketch = 0
   pn = 0x10
   try:
    for c in range(0,10):
     pmeid = self.pme.beginTransmission(pn)
     if pmeid != 0:
      break
     time.sleep(0.01)
    if pmeid != 0:
     carr = [pn,0,0,0]
     self.pme.write(bytes(carr),pmeid)
     time.sleep(0.001)
     data = self.pme.read(4,pmeid) # read data
     self.pme.endTransmission(pmeid)
     if len(data)>3:
      if int(data[0]) == pn and int(data[1]) == 0xfe and int(data[2]) != 0 and int(data[2]) != 0xff: # check sketch version packet validity
       sketch = int(data[3])
   except Exception as e:
    if pmeid != 0:
     self.pme.endTransmission(pmeid)
    sketch = 0
   return sketch

