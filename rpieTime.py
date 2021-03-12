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
import misc

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
    upts = misc.formatnum( ((rs.days * 86400) + rs.seconds)/60, 4)
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
  self.looping = False
  self.loopcount = 0
  self.maxloops = -1
  self.timeout = 0
  self.laststart = 0
  self.lasterr = ""

 def addcallback(self,callback):
  self.retvalue = [-1,-1]
  self.callback = callback

 def setretvalue(self,retvalue):
  self.retvalue = retvalue

 def __del__(self):
  if self.timer:
   try:
    self.timer.cancel()
   except:
    pass

 def start(self,timeout,usrcall=True,looping=False,maxloops=-1):
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Timer "+str(self.timerid)+" started with timeout: "+str(timeout))
  try:
   if self.timer is not None:
    try:
     self.timer.cancel()
    except:
     pass
    self.timer = None
   self.starttime = time.time()
   self.lefttime  = timeout
   self.state = 1
   self.timeractive = True
   self.looping = looping
   if usrcall or self.timeout==0:
    self.timeout = timeout
    self.maxloops = maxloops
    self.loopcount = 0
   self.loopcount += 1
   self.laststart = time.time()
   self.timer = Timer(float(timeout),self.stop)
   self.timer.start()
   self.lasterr = ""
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Timer "+str(self.timerid)+" error: "+str(e))
   self.lasterr = str(e)

 def stop(self,call=True):
  misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Timer "+str(self.timerid)+" stopped")
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
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Timer "+str(self.timerid)+" error: "+str(e))
   self.lasterr = str(e)
  if self.maxloops>-1:
   if self.loopcount>=self.maxloops: #loop count reached
    self.looping = False
  if self.looping and call: #autorestart timer
   self.start(self.timeout,False,True,self.maxloops)
  else:
   self.looping = False

 def pause(self):
  if self.state == 1:
   lefttime = time.time()-self.starttime
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Timer "+str(self.timerid)+" running paused at "+str(lefttime))
   if lefttime<self.lefttime:
    self.lefttime = self.lefttime - lefttime
    self.state = 2
    try:
     self.timer.cancel()
    except:
     pass

 def resume(self):
  if self.state == 2:
   misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG, "Timer "+str(self.timerid)+" running continues for "+str(self.lefttime))
   try:
    self.timer = Timer(self.lefttime,self.stop)
    self.starttime = time.time()
    self.state = 1
    self.pausetime = 0
    self.timer.start()
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR, "Timer "+str(self.timerid)+" error: "+str(e))

def addsystemtimer(timeout,callbackfunc,retvaluearray):
 result = False
 for t in range(0,rpieGlobals.SYSTEM_TIMER_MAX):
  if SysTimers[t].timeractive==False:
   try:
    SysTimers[t].addcallback(callbackfunc)
    SysTimers[t].setretvalue(retvaluearray)
    SysTimers[t].start(timeout)
    result = True
    break
   except:
    pass
 if result==False:
  misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"No more system timers for: "+str(retvaluearray))
 return result

Timers = []
for t in range(0,rpieGlobals.RULES_TIMER_MAX):
 Timers.append(timer(t+1))

SysTimers = []
for t in range(0,rpieGlobals.SYSTEM_TIMER_MAX):
 SysTimers.append(timer(t))
