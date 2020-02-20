#!/usr/bin/env python3
#############################################################################
#################### MPU9150/9250 plugin for RPIEasy ########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import time
import RTIMU
import gpios
import math
import threading

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 207
 PLUGIN_NAME = "Gyro - MPU9150/9250 (TESTING)"
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
  self.lastdet  = 0
  self.mpu = None
  self.lastmove = 0
  self.s = None
  self.interval2 = 0
  self.cachedvals = [0,0,0]

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.timer100ms = False
  self.initialized = False
  self.readinprogress = False
  self.lastread = 0
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
      self.s = RTIMU.Settings("RTIMULib")
      self.mpu = RTIMU.RTIMU(self.s)
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"MPU: "+str(self.mpu.IMUName()))
      self.initialized = self.mpu.IMUInit()
     except Exception as e:
      self.mpu = None
   if (self.mpu is None) or self.initialized==False:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MPU can not be initialized! ")
    return False
   else:
    self.mpu.setSlerpPower(0.02)
    self.mpu.setGyroEnable(True)
    self.mpu.setAccelEnable(True)
    self.mpu.setCompassEnable(True)
    self.interval2 = 0.1
    self.enabled=False
    time.sleep(1)
    self.enabled=True
    if self.interval==0:
      self.timer100ms = True # enable periodic check if interval not specified
      self.interval2 = 0.1
    elif self.interval < 2:
      self.interval2 = 0.5
    elif self.interval < 60:
      self.interval2 = 1
    else:
      self.interval2 = 5
    bgt = threading.Thread(target=self.bgreader)
    bgt.daemon = True
    bgt.start()

 def bgreader(self):
   while self.enabled:
    if self.initialized:
     try:
      readok = True
      if self.mpu.IMURead()==False:
       readok = False
       self.mpu.IMUInit()
       time.sleep(0.1)
       readok = self.mpu.IMURead()
      if readok:
       data = self.mpu.getIMUData()
       fusionPose = data["fusionPose"]
       self.cachedvals[0] = int(float(math.degrees(fusionPose[0])))
       self.cachedvals[1] = int(float(math.degrees(fusionPose[1])))
       self.cachedvals[2] = int(float(math.degrees(fusionPose[2])))
       self.lastread = time.time()
     except Exception as e:
      pass
     time.sleep(self.interval2)
    else:
     time.sleep(0.1)

 def webform_load(self): # create html page for settings
   choice0 = int(self.taskdevicepluginconfig[0])
   options = ["Nothing","Roll","Pitch","Yaw"]
   optionvalues = [0,1,2,3]
   webserver.addFormSelector("Type","p207_function0",len(optionvalues),options,optionvalues,None,choice0)
   choice1 = int(self.taskdevicepluginconfig[1])
   webserver.addFormSelector("Type","p207_function1",len(optionvalues),options,optionvalues,None,choice1)
   choice2 = int(self.taskdevicepluginconfig[2])
   webserver.addFormSelector("Type","p207_function2",len(optionvalues),options,optionvalues,None,choice2)
   if self.enabled and self.initialized:
    try:
      data = self.mpu.getIMUData()
      webserver.addFormNote("Gyro valid: "+str(data["gyroValid"]))
      webserver.addFormNote("Accel valid: "+str(data["accelValid"]))
      webserver.addFormNote("Compass valid: "+str(data["compassValid"]))
    except:
      pass
   return True

 def webform_save(self,params): # process settings post reply
   par = webserver.arg("p207_function0",params)
   try:
    self.taskdevicepluginconfig[0] = int(par)
    if int(par)==0:
     self.vtype=rpieGlobals.SENSOR_TYPE_SWITCH
    else:
     self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1
   except:
    self.taskdevicepluginconfig[0] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1

   par = webserver.arg("p207_function1",params)
   try:
    self.taskdevicepluginconfig[1] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_DUAL
    self.valuecount=2
   except:
    self.taskdevicepluginconfig[1] = 0
    self.vtype=rpieGlobals.SENSOR_TYPE_SINGLE
    self.valuecount=1

   par = webserver.arg("p207_function2",params)
   try:
    self.taskdevicepluginconfig[2] = int(par)
    self.vtype=rpieGlobals.SENSOR_TYPE_TRIPLE
    self.valuecount=3
   except:
    self.taskdevicepluginconfig[2] = 0

   return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.enabled and self.initialized:
   try:
     val = int(self.taskdevicepluginconfig[0])
     if val>0:
      val = val-1
      self.set_value(1,self.cachedvals[val],False)
     val = int(self.taskdevicepluginconfig[1])
     if val>0:
      val = val-1
      self.set_value(2,self.cachedvals[val],False)
     val = int(self.taskdevicepluginconfig[2])
     if val>0:
      val = val-1
      self.set_value(3,self.cachedvals[val],False)
     if time.time()-self.lastread<self.interval:
      result = True
     else:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"MPU readout too old!")
   except Exception as e:
    pass
   if result:
     self._lastdataservetime = rpieTime.millis()
     self.plugin_senddata()
  return result

 def timer_ten_per_second(self):
  if self.enabled and self.initialized:
   changed = False
   try:
    if time.time()-self.lastdet>0.3:
     val = int(self.taskdevicepluginconfig[0])
     if val>0:
      val = val-1
      rval = self.cachedvals[val]
      if abs(int(float(self.uservar[0]))-rval)>5:
       self.set_value(1,rval,False)
       changed = True
     val = int(self.taskdevicepluginconfig[1])
     if val>0:
      val = val-1
      rval = self.cachedvals[val]
      if abs(int(float(self.uservar[1]))-rval)>5:
       self.set_value(2,rval,False)
       changed = True
     val = int(self.taskdevicepluginconfig[2])
     if val>0:
      val = val-1
      rval = self.cachedvals[val]
      if abs(int(float(self.uservar[2])-rval))>5:
       self.set_value(3,rval,False)
       changed = True
   except Exception as e:
    pass
   if changed:
     self.lastdet = time.time()
     self.plugin_senddata()
  return self.timer100ms
