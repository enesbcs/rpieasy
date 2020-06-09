#!/usr/bin/env python3
#############################################################################
################# Helper Library for RPi GPIO Keypad ########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import RPi.GPIO as GPIO
import time
import threading

class keypad():
 def __init__(self,keypad=[],row_pins=[],col_pins=[],callback=None):
   if len(keypad)<1 or len(row_pins)<1 or len(col_pins)<1:
    return
   self.keypad = keypad
   self.rowpins = row_pins
   self.colpins = col_pins
   self.callback = callback
   self.readmode = 0
   self.initpins()
   self.initialized = True

 def initpins(self):
#   GPIO.setwarnings(False)
#   GPIO.setmode(GPIO.BCM)
   for po in self.colpins:
    GPIO.setup(po,GPIO.OUT)
   for pi in self.rowpins:
    GPIO.setup(pi,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    try:
     GPIO.remove_event_detect(pi)
    except:
     pass
    time.sleep(0.05)
    GPIO.add_event_detect(pi,GPIO.RISING, callback=self.inthandler,bouncetime=200)

 def isInitialized(self):
   return self.initialized

 def inthandler(self,channel):
   if channel in self.rowpins:
    if self.readmode==1:
     self.getButton()

 def setup_keyscan(self):
  for p in self.colpins:
   GPIO.output(p,1)
  self.readmode = 1

 def startscan(self):
   bgt = threading.Thread(target=self.scanproc)
   bgt.daemon = True
   bgt.start()

 def scanproc(self):
   while self.initialized:
    if self.readmode==0:
     self.setup_keyscan()
    else:
     time.sleep(0.2)

 def stopscan(self):
  self.initialized = False
  try:
   for pi in self.rowpins:
    GPIO.remove_event_detect(pi)
  except:
   pass

 def getButton(self):
    self.readmode=2
    result = None
    resultCoordx = -1
    resultCoordy = -1
    rstart = time.time()
    while result == None and self.initialized:
     try:
      for actCol in self.colpins:
        resultCoordy+=1
        for _actCol in self.colpins:
          GPIO.output(_actCol, 0)
        GPIO.output(actCol, 1)
        for actLine in self.rowpins:
          resultCoordx += 1
          if GPIO.input(actLine):
            result = self.keypad[resultCoordx][resultCoordy]
          time.sleep(0.005)
        resultCoordx = -1
        time.sleep(0.005)
      resultCoordy = -1
      time.sleep(0.005)
      if time.time()-rstart>2:
       break
     except:
      pass
    self.readmode = 0
    if self.callback is not None:
     try:
      self.callback(result)
     except:
      pass
    return result

