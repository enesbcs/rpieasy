#!/usr/bin/env python3
#############################################################################
####################### Helper library for Blynk  ###########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import blynklib
import commands
import rpieGlobals
import time

blynk = blynklib.Blynk("",server="127.0.0.1",port=0,heartbeat=0)
blynkconnected = False
vpinhandlers = []

@blynk.handle_event("connect")
def connect_handler():
  global blynkconnected
  blynkconnected = True
  commands.rulesProcessing("blynk_connected",rpieGlobals.RULE_SYSTEM)

@blynk.handle_event("disconnect")
def disconnect_handler():
  global blynkconnected
  blynkconnected = False
  commands.rulesProcessing("blynk_disconnected",rpieGlobals.RULE_SYSTEM)

@blynk.handle_event('write V*')
def write_pin_handler(pin,value):
  global vpinhandlers
  for i in range(len(vpinhandlers)):
   try:
    func = vpinhandlers[i]
    if func is not None:
     func(pin,value)
   except:
    pass

def addhandler(callback):
  global vpinhandlers
  if not callback in vpinhandlers:
   vpinhandlers.append(callback)

def removehandler(callback):
  global vpinhandlers
  if callback in vpinhandlers:
   vpinhandlers.remove(callback)

def BlynkLoop(): # Blynk background loop, started at a separated thread
 global blynk, blynkconnected
 while True:
  if blynkconnected and blynk is not None:
   blynk.run()
  else:
   time.sleep(2)
