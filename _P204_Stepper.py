#!/usr/bin/env python3
#############################################################################
################ Stepper motor driver plugin for RPIEasy ####################
#############################################################################
#
# Stepper motor driver by 4 GPIO connection based on code written by Stephen C Phillips. ( http://scphillips.com )
#
# Available commands: (for example http or rules based controlling)
#
# motor,<taskname>,pos,<angle>    - Set the motor named "taskname" to "angle" (0-360) position from a fixed ZERO position
#                                   angle can be number between 0-360 or HOME,LAST,N,E,S,W
#
# motor,<taskname>,setzero        - Set the current position of the motor as ZERO
#
# motor,<taskname>,left,<angle>   - Rotate the motor named "taskname" with "angle" (0-360) from current position - Anti-clockwise
# motor,<taskname>,right,<angle>  - Rotate the motor named "taskname" with "angle" (0-360) from current position - Clockwise
#
# motor,<taskname>,pan,<startangle>,<stopangle>,<delay>,<speed>
#   - Pan the motor named "taskname" continously between "startangle" and "stopangle", staying off for "delay" second in between
#     and speed can be 1-20
#
# motor,<taskname>,off            - Sets the motor off - pull all 4 gpio to low (otherwise it consumes energy while standing)
#                                   (also stops panning immediately but relative position can be messed if used, use panstop instead)
# motor,<taskname>,panstop         - Sets the motor stop panning after finishing it's current move
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
from lib.Stepper.Stepper import Motor
import threading
import time
import Settings

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 204
 PLUGIN_NAME = "Output - Stepper driver (TESTING)"
 PLUGIN_VALUENAME1 = "Angle"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_QUAD
  self.vtype = rpieGlobals.SENSOR_TYPE_SINGLE
  self.valuecount = 1
  self.senddataoption = False
  self.recdataoption = True
  self.timeroption = False
  self.formulaoption = False
  self.motor = None
  self.bgproc = None
  self.panning = False
  self.panstart = 20
  self.panstop = 340
  self.pandelay = 3
  self.lastpos = 0

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.initialized = False
  if self.enabled and self.taskdevicepin[0]>0 and self.taskdevicepin[1]>0 and self.taskdevicepin[2]>0 and self.taskdevicepin[3]>0:  
   if self.motor and self.motor is not None:
    try:
     mangle = self.getangle(self.motor.step_angle)
     if mangle != int(self.uservar[0]):
      self.motor.step_angle = float(self.uservar[0])
     self.initialized = True
    except Exception as e:
     self.initialized = False
   if self.initialized == False:
    try:
     self.motor = Motor([int(self.taskdevicepin[0]),int(self.taskdevicepin[1]),int(self.taskdevicepin[2]),int(self.taskdevicepin[3])],int(self.taskdevicepluginconfig[0]))
     self.initialized = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Stepper motor can not be initialized: "+str(e))
     self.initialized = False
     self.enabled = False
   if self.initialized:
     self.panning = False
     self.bgproc = None

 def plugin_exit(self):
  self.panning = False
  try:
   self.motorpos(0)
   self.motor.stop()
  except:
   pass

 def __del__(self):
  self.plugin_exit()

 def webform_load(self):
  webserver.addFormNote("Set 4 pins to OUTPUT <a href='pinout'>at pinout</a> first, than specify them here.")
  webserver.addFormNumericBox("Speed","p204_speed",self.taskdevicepluginconfig[0],1,25)
  return True

 def webform_save(self,params):
  par = webserver.arg("p204_speed",params)
  if par=="" or int(par)<1:
   par = 1
  self.taskdevicepluginconfig[0] = int(par)
  return True

 def plugin_receivedata(self,data):       # Watching for incoming mqtt commands
  if (len(data)>0):
   try:
    av = int(data[0])
   except:
    av = -360
   if av>-360 and av<360:
    self.set_value(1,av,False)

 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized and self.enabled:
   try:
    self.motorpos(value)
   except:
    pass
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def motorpos(self,pos):
   self.motor.move_to(int(pos))
   self.lastpos = self.uservar[0]
   self.uservar[0] = self.getangle(self.motor.step_angle)

 def plugin_write(self,cmd):                                                # Handling commands
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0]== "motor":
   subcmd = ""
   rname = ""
   if self.motor is not None:
    try:
     rname = cmdarr[1].strip()
     subcmd = cmdarr[2].strip()
    except:
     rname = ""
    try:
      angle = int(float(cmdarr[3].strip()))
    except:
      angle = -360
    try:
      speed = int(cmdarr[4].strip())
    except:
      speed = 0
    if speed==0:
     speed = int(self.taskdevicepluginconfig[0])
   if rname.lower()=="all": # this command is for every motor
    if subcmd.lower() in ["off","panstop"]:
     for x in range(0,len(Settings.Tasks)):
      try:
       if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool:
        if (Settings.Tasks[x].enabled) and (Settings.Tasks[x].PLUGIN_ID==self.PLUGIN_ID):
         if subcmd.lower() == "off":
          Settings.Tasks[x].panning = False
          Settings.Tasks[x].motor.stop()
         elif subcmd.lower() == "panstop":
          Settings.Tasks[x].panning = False
      except:
        pass
     return True
   if self.taskname.lower() == rname.lower(): # this command is for us
    res = True
    if subcmd.lower() == "pos":
     if angle==-360:
      astr = cmdarr[3].strip().lower()
      if astr == "home" or astr=="n":
       angle = 0
      elif astr == "last":
       angle = self.lastpos
      elif astr == "e":
       angle = 90
      elif astr == "s":
       angle = 180
      elif astr == "w":
       angle = 270
      elif astr == "ne":
       angle = 45
      elif astr == "se":
       angle = 135
      elif astr == "nw":
       angle = 315
      elif astr == "sw":
       angle = 225
     if angle> -360:
      self.motor.setspeed(speed)
      self.motor.move_to(angle)
    elif subcmd.lower() == "left": # acw
     if angle> -360:
      self.motor.setspeed(speed)
      self.motor.move_acw(angle)
    elif subcmd.lower() == "right": # cw
     if angle> -360:
      self.motor.setspeed(speed)
      self.motor.move_cw(angle)
    elif subcmd.lower() == "off":
      self.panning = False
      try:
       self.motor.stop()
      except:
       pass
    elif subcmd.lower() == "panstop":
      self.panning = False
    elif subcmd.lower() == "setzero":
      self.panning = False
      try:
       self.motor.stop()
       self.uservar[0] = 0
       self.motor.step_angle = 0
       self.motor.step_angle2 = 0
      except:
       pass
    elif subcmd.lower() == "pan":
     if angle>-360:
      self.panstart = angle # starting angle
      self.panstop = speed  # ending angle
      try:
       b = int(cmdarr[5].strip())
      except:
       b = -1
      if b>=0:
       self.pandelay = b
      speed = 0
      try:
        speed = int(cmdarr[6].strip())
      except:
        speed = 0
     if speed==0:
       speed = int(self.taskdevicepluginconfig[0])
     if self.panning:
      self.panning = False
      time.sleep(3)
     self.bgproc = threading.Thread(target=self.backgroundpanning)
     self.bgproc.daemon = True
     self.motor.setspeed(speed)
     self.panning = True
     self.bgproc.start()
    self.lastpos = self.uservar[0]
    self.uservar[0] = self.getangle(self.motor.step_angle)
  return res

 def getangle(self,step_angle):
   return step_angle

 def backgroundpanning(self):
  direction = False
  angle = abs(self.panstart-self.panstop)
  if self.panstop<self.panstart:
   self.motor.move_to(self.panstop)
  else:
   self.motor.move_to(self.panstart)
  self.uservar[0] = self.getangle(self.motor.step_angle)
  time.sleep(1)
  while self.panning:
   try:
    if direction:
      self.motor.move_acw(angle)
    else:
      self.motor.move_cw(angle)
   except:
    self.panning = False
   self.motor.stop()
   self.uservar[0] = self.getangle(self.motor.step_angle)
   direction = not direction
   time.sleep(self.pandelay)
