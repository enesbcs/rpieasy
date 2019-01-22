#!/usr/bin/env python3
#############################################################################
################### Pro Mini Extender plugin for RPIEasy ####################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import fcntl
import time
import Settings

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 11
 PLUGIN_NAME = "Extra IO - ProMini Extender (TESTING)"
 PLUGIN_VALUENAME1 = "Value"

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
      self.pme = PME(i2cport,dport)
     except Exception as e:
      self.pme = None
   if self.pme:
    try:
     self.initialized = self.pme.init
    except:
     self.pme = None
   if self.pme is None:
    self.enabled = False
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"PME can not be initialized! "+str(e))
    return False
   else:
    if self.interval>0:
     self.timer100ms = False # normal read
    else:
     self.uservar[0] = -1
     self.readinprogress = 0
     self.timer100ms = True  # oversampling method
    if str(self.taskdevicepluginconfig[1])=="1":
     self.timer100ms = False # oversampling will not work for analog read

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
   linefree = True
   for s in range(len(Settings.Tasks)):
    if Settings.Tasks[s] and type(Settings.Tasks[s]) is not bool:
     if Settings.Tasks[s].pluginid == self.pluginid:
      if Settings.Tasks[s].enabled and Settings.Tasks[s].readinprogress==1:
       linefree = False
       break
   if linefree:
    self.readinprogress = 1
    try:
     pt = int(self.taskdevicepluginconfig[1])
     pn = int(self.taskdevicepluginconfig[2])
     result = self.pme.read(pt,pn)
     self.set_value(1,result,True)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.readinprogress = 0
    self._lastdataservetime = rpieTime.millis()
    result = True
  return result

 def timer_ten_per_second(self):
  if self.readinprogress == 0 and self.timer100ms:
   self.readinprogress = 1
   try:
    pt = int(self.taskdevicepluginconfig[1])
    pn = int(self.taskdevicepluginconfig[2])
    result = self.pme.read(pt,pn)
    if float(result)!=float(self.uservar[0]):
     self.set_value(1,result,True)
   except Exception as e:
    print(e)
   self.readinprogress = 0
  return self.timer100ms

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
     self.pme.write(0,pin,val)
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
     self.pme.write(1,pin,prop)
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
     self.pme.write(0,pin,val)
     s = (dur/1000)
     time.sleep(s)
     self.pme.write(0,pin,(1-val))
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
     self.pme.write(0,pin,val)
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
     self.pme.write(0,ioarray[0],ioarray[1])
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"EXTGPIO"+str(ioarray[0])+": "+str(e))

class PME:

 I2C_SLAVE = 0x0703
 I2C_SLAVE_FORCE = 0x0706
 CMD_DIGITAL_WRITE = 1
 CMD_DIGITAL_READ  = 2
 CMD_ANALOG_WRITE  = 3
 CMD_ANALOG_READ   = 4

 def __init__(self, device_number=1,i2ca=0x3f):
     self.i2caddress = int(i2ca)
     try:
      self.i2cr = open("/dev/i2c-"+str(device_number),"rb",buffering=0)
      self.i2cw = open("/dev/i2c-"+str(device_number),"wb",buffering=0)
      fcntl.ioctl(self.i2cr, self.I2C_SLAVE,self.i2caddress)
      fcntl.ioctl(self.i2cw, self.I2C_SLAVE,self.i2caddress)
      self.init = True
     except:
      self.init = False

 def read(self,ptype,pnum):
  if self.init:
   try:
    pnum = int(pnum) & 0xFF
    ptype = int(ptype)
   except:
    return False
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
   barr = bytes(carr)
#   print("send data",barr) # DEBUG
   self.i2cw.write(barr)    # send read data command
   if ptype==0:
    time.sleep(0.001)  # digital read is almost instantous
   else:
    time.sleep(0.015)   # analog read takes more time
   data = self.i2cr.read(4) # read data
#   print("rec data",data) # DEBUG
   if len(data)>0:
    if ptype==0:
     return data[0]
    elif len(data)>1:
     return (data[1] << 8 | data[0]) # 0-1023
  return 0

 def write(self,ptype,pnum,value):
  # ptype 0=digital,1=analog
  if self.init:
   try:
    pnum = int(pnum) & 0xFF
    ptype = int(ptype)
   except:
    return False
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
#   print("send data",carr)
   self.i2cw.write(bytes(carr))    # send write data command
  return True

 def close(self):
     if self.init:
      self.i2cr.close()
      self.i2cw.close()

 def __enter__(self):
     return self

 def __exit__(self, type, value, traceback):
     self.close()
