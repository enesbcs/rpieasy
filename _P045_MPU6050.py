#!/usr/bin/env python3
#############################################################################
###################### MPU6050 plugin for RPIEasy ###########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import time
import lib.lib_mpurouter as mpurouter

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 45
 PLUGIN_NAME = "Gyro - MPU6050 (TESTING)"
 PLUGIN_VALUENAME1 = "Value1"
 PLUGIN_VALUENAME2 = "Value2"
 PLUGIN_VALUENAME3 = "Value3"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.readinprogress = 0
  self.valuecount = 1
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = True
  self.formulaoption = True
  self._nextdataservetime = 0
  self.lastread = 0
  self.mpu = None
  self.lastmove = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.initialized = False
  self.timer1s = False
  if self.enabled:
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
      dport = int(self.taskdevicepluginconfig[0])
     except:
      dport = 0
     if dport == 0:
      dport = 0x68
      self.mpu = None
     try:
      self.mpu = mpurouter.request_mpu_device(busnum=int(i2cl),i2caddress=dport)
      self.initialized = self.mpu.initialized
     except Exception as e:
      self.mpu = None
   if (self.mpu is None) or self.initialized==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MPU6050 can not be initialized! ")
    return False
   else:
    self.mpu.buf_read()
#    self.timer1s = True
    self.lastmove = 0
    if self.taskdevicepin[0]>=0:
     self.__del__()
     try:
      gpios.HWPorts.add_event_detect(self.taskdevicepin[0],gpios.FALLING,self.p045_handler)
      self.timer1s = False
     except Exception as e:
      self.timer1s = True
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Interrupt error "+str(e)) 
    else:
     if str(self.taskdevicepluginconfig[1])=="0" or self.interval==0:
      self.timer1s = True

 def __del__(self):
   if self.taskdevicepin[0]>=0 and self.enabled:
    try:
     gpios.HWPorts.remove_event_detect(self.taskdevicepin[0])
    except:
     pass

 def plugin_exit(self):
  self.__del__()
  return True

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x68","0x69"]
  optionvalues = [0x68,0x69]
  webserver.addFormSelector("I2C address","p045_address",len(optionvalues),options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  webserver.addFormPinSelect("Interrupt pin","p045_int_pin",self.taskdevicepin[0])
  webserver.addFormNote("Set an Input-PULLUP pin to INT pin and connect it for fastest results. (optional)")
  choice2 = int(self.taskdevicepluginconfig[1])
  options = ["Movement detection","Acceleration X","Acceleration Y","Acceleration Z","G-force X","G-force Y","G-force Z"]
  optionvalues = [0,4,5,6,7,8,9]
  webserver.addFormSelector("Type","p045_function",len(optionvalues),options,optionvalues,None,choice2)
  if choice2==0:
   webserver.addHtml("<TR><TD><TD>The thresholdvalues (-65535 to 65535, except 0) can be used to set a threshold for one or more<br>")
   webserver.addHtml("axis. The axis will trigger when the range for that axis exceeds the threshold<br>")
   webserver.addHtml("value. A value of 0 disables movement detection for that axis.")
   webserver.addFormNumericBox("Detection threshold X", "p045_threshold_x", self.taskdevicepluginconfig[2], -65535, 65535)
   webserver.addFormNumericBox("Detection threshold Y", "p045_threshold_y", self.taskdevicepluginconfig[3], -65535, 65535)
   webserver.addFormNumericBox("Detection threshold Z", "p045_threshold_z", self.taskdevicepluginconfig[4], -65535, 65535)
   webserver.addFormNumericBox("Min movement time", "p045_threshold_window", self.taskdevicepluginconfig[6], 0, 120)
   webserver.addUnit("s")
  else: # pos
   choice5 = int(self.taskdevicepluginconfig[7])
   options = ["Nothing","Acceleration X","Acceleration Y","Acceleration Z","G-force X","G-force Y","G-force Z"]
   optionvalues = [0,4,5,6,7,8,9]
   webserver.addFormSelector("Type","p045_function2",len(optionvalues),options,optionvalues,None,choice5)
   choice6 = int(self.taskdevicepluginconfig[8])
   webserver.addFormSelector("Type","p045_function3",len(optionvalues),options,optionvalues,None,choice6)
  if self.enabled and self.initialized:
   try:
    webserver.addFormNote("Accel x:"+str(self.mpu.ax)+", y:"+str(self.mpu.ay)+", z:"+str(self.mpu.az))
    webserver.addFormNote("Gyro x:"+str(self.mpu.gx)+", y:"+str(self.mpu.gy)+", z:"+str(self.mpu.gz))
   except:
    pass
  return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p045_addr",params)
   if par == "":
    par = 0x68
   self.taskdevicepluginconfig[0] = int(par)

   par = webserver.arg("p045_int_pin",params)
   if par == "":
    par = -1
   self.taskdevicepin[0] = int(par)

   par = webserver.arg("p045_function",params)
   try:
    self.taskdevicepluginconfig[1] = int(par)
    if int(par)==0:
     self.vtype=rpieGlobals.SENSOR_TYPE_SWITCH
    else:
     self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1
   except:
    self.taskdevicepluginconfig[1] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1

   par = webserver.arg("p045_function2",params)
   try:
    self.taskdevicepluginconfig[7] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_DUAL
    self.valuecount=2
   except:
    self.taskdevicepluginconfig[7] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1

   par = webserver.arg("p045_function3",params)
   try:
    self.taskdevicepluginconfig[8] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_TRIPLE
    self.valuecount=3
   except:
    self.taskdevicepluginconfig[8] = 0

   par = webserver.arg("p045_threshold_x",params)
   try:
    self.taskdevicepluginconfig[2] = int(par)
   except:
    self.taskdevicepluginconfig[2] = 0

   par = webserver.arg("p045_threshold_y",params)
   try:
    self.taskdevicepluginconfig[3] = int(par)
   except:
    self.taskdevicepluginconfig[3] = 0

   par = webserver.arg("p045_threshold_z",params)
   try:
    self.taskdevicepluginconfig[4] = int(par)
   except:
    self.taskdevicepluginconfig[4] = 0

   par = webserver.arg("p045_threshold_counter",params)
   try:
    self.taskdevicepluginconfig[5] = int(par)
   except:
    self.taskdevicepluginconfig[5] = 0

   par = webserver.arg("p045_threshold_window",params)
   try:
    self.taskdevicepluginconfig[6] = int(par)
   except:
    self.taskdevicepluginconfig[6] = 0

   if self.taskdevicepluginconfig[6] < self.taskdevicepluginconfig[5]:
    self.taskdevicepluginconfig[6] = self.taskdevicepluginconfig[5]

   return True

 def p045_handler(self,channel):
  if int(self.taskdevicepluginconfig[1])==0: # motion detection
   self.timer_once_per_second()
  else:
   self.plugin_read()

 def timer_once_per_second(self):
  if self.enabled and self.initialized:
    try:
     self.mpu.buf_read()
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MPU6050: "+str(e))
     self.initialized = False
    if int(self.taskdevicepluginconfig[1])==0: # motion detection
     motion = 0
     if self.taskdevicepluginconfig[2]!=0 and self.mpu.ax > self.taskdevicepluginconfig[2]:
      motion = 1
     else:
      if self.taskdevicepluginconfig[3]!=0 and self.mpu.ay > self.taskdevicepluginconfig[3]:
       motion = 1
      else:
       if self.taskdevicepluginconfig[4]!=0 and self.mpu.az > self.taskdevicepluginconfig[4]:
        motion = 1
     if int(motion) != int(float(self.uservar[0])):
      if motion==1:
       self.lastmove = time.time()
       rpieTime.addsystemtimer(int(self.taskdevicepluginconfig[6]),self.p045_timercb,[-1])
      elif (time.time()-self.lastmove)<self.taskdevicepluginconfig[6]:
       return False
      self.set_value(1,motion,True)

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  val1 = None
  if self.enabled and self.initialized:
    try:
     self.mpu.buf_read()
    except:
     pass
    if int(self.taskdevicepluginconfig[1])==0: # motion detection
     motion = 0
     if self.taskdevicepluginconfig[2]!=0 and self.mpu.ax > self.taskdevicepluginconfig[2]:
      motion = 1
     else:
      if self.taskdevicepluginconfig[3]!=0 and self.mpu.ay > self.taskdevicepluginconfig[3]:
       motion = 1
      else:
       if self.taskdevicepluginconfig[4]!=0 and self.mpu.az > self.taskdevicepluginconfig[4]:
        motion = 1
     val1 = motion
     self.set_value(1,val1,False)
    else:
     val1 = self.getvalue(self.taskdevicepluginconfig[1])
     self.set_value(1,val1,False)
     if int(self.taskdevicepluginconfig[7])!=0:
      self.set_value(2,self.getvalue(self.taskdevicepluginconfig[7]),False)
     if int(self.taskdevicepluginconfig[8])!=0:
      self.set_value(3,self.getvalue(self.taskdevicepluginconfig[8]),False)
    if val1 is not None:
     self._lastdataservetime = rpieTime.millis()
     self.plugin_senddata()
    result = True
  return result

 def getvalue(self,valid):
  val1 = None
  if valid!=0:
    if int(valid)==4:
     val1 = self.mpu.ax
    elif int(valid)==5:
     val1 = self.mpu.ay
    elif int(valid)==6:
     val1 = self.mpu.az
    elif int(valid)==7:
     val1 = self.mpu.gx
    elif int(valid)==8:
     val1 = self.mpu.gy
    elif int(valid)==9:
     val1 = self.mpu.gz
  return val1

 def p045_timercb(self,stimerid):
  self.timer_once_per_second()
