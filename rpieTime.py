#!/usr/bin/env python3
#############################################################################
###################### Helper Library for Time functions ####################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
from datetime import datetime
from datetime import timedelta
from threading import Timer
import time
import rpieGlobals

start_time = datetime.now()

def millis():
   global start_time
   dt = datetime.now() - start_time
   ms = int((dt.days * 86400000) + (dt.seconds * 1000) + (dt.microseconds / 1000))
   return ms

def getuptime(form=0):
   global start_time
   rs = datetime.now() - start_time
   upts = ""
   if form==0:
    upts = (rs.days * 86400) + rs.seconds
   elif form==1:
    hours, remainder = divmod(rs.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    upts = str(rs.days) + " days " + str(hours) + " hours " + str(minutes) + " minutes"
   elif form==2:
    upts = ((rs.days * 86400) + rs.seconds)/60
   return upts

class timer:
 def __init__(self,timerid):
  self.timerid = timerid
  self.state = 0 # 0:off,1:running,2:paused
  self.starttime = 0
  self.pausetime = 0
  self.lefttime  = 0
  self.timer = None
  self.timeractive = False
  self.callback = None
  self.retvalue = [-1,-1]

 def addcallback(self,callback):
  self.retvalue = [-1,-1]
  self.callback = callback

 def setretvalue(self,retvalue):
  self.retvalue = retvalue

 def __del__(self):
  if self.timer:
   self.timer.cancel()

 def start(self,timeout):
#  print("Timer",self.timerid,"started with timeout:",timeout)
  try:
   if self.timer is not None:
    self.timer.cancel()
    self.timer = None
   self.starttime = time.time()
   self.lefttime  = timeout
   self.state = 1
   self.timeractive = True
   self.timer = Timer(float(timeout),self.stop)
   self.timer.start()
  except Exception as e:
   print(e)

 def stop(self,call=True):
#  print("Timer",self.timerid,"stopped")
  self.state = 0
  self.starttime = 0
  self.timeractive = False
  try:
   if self.timer is not None:
    self.timer.cancel()
  except:
   pass
  try:
   if call and self.callback:
    if self.retvalue[0] > -1:
     self.callback(self.timerid,self.retvalue) # callbacks with saved return value
    else:
     self.callback(self.timerid) # call rules with timer id only
  except Exception as e:
   print(e)

 def pause(self):
  if self.state == 1:
   lefttime = time.time()-self.starttime
#   print("Timer",self.timerid,"runnning paused at",lefttime)
   if lefttime<self.lefttime:
    self.lefttime = self.lefttime - lefttime
    self.state = 2
    self.timer.cancel()

 def resume(self):
  if self.state == 2:
#   print("Timer",self.timerid,"runnning continues for",self.lefttime)
   self.timer = Timer(self.lefttime,self.stop)
   self.starttime = time.time()
   self.state = 1
   self.pausetime = 0
   self.timer.start()

def addsystemtimer(timeout,callbackfunc,retvaluearray):
 result = False
 for t in range(0,rpieGlobals.SYSTEM_TIMER_MAX):
  if SysTimers[t].timeractive==False:
   SysTimers[t].addcallback(callbackfunc)
   SysTimers[t].setretvalue(retvaluearray)
   SysTimers[t].start(timeout)
   result = True
   break
 if result==False:
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"No more system timers for: "+str(retvaluearray))
 return result

Timers = []
for t in range(0,rpieGlobals.RULES_TIMER_MAX):
 Timers.append(timer(t+1))

SysTimers = []
for t in range(0,rpieGlobals.SYSTEM_TIMER_MAX):
 SysTimers.append(timer(t))
