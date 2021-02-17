#!/usr/bin/env python3
#############################################################################
##################### Helper Library for PMSx003 ############################
#############################################################################
#
# Copyright (C) 2021 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
from pms.sensor import SensorReader
import time

class PMSEntity():
 def __init__(self,devtype,serialp):
  self.devtype = devtype
  self.serialp = serialp
  self.connected = False
  self.readinprogress = False
  self.lastread = ""
  try:
   self.pms = SensorReader(devtype,serialp)
  except Exception as e:
   self.pms = None

 def connect(self,force=False):
  if self.connected==False or force:
   try:
    self.pms.__enter__()
    self.connected = True
    self.readinprogress = False
   except Exception as e:
    self.connected = False

 def disconnect(self,force=False):
  if self.connected or force:
   try:
    self.pms.__exit__(0,0,0)
   except:
    pass
   self.connected = False

 def is_open(self):
  try:
   return self.pms.serial.is_open
  except Exception as e:
   return False

 def readdata(self):
   if self.connected==False:
    return None
   if self.readinprogress==False:
    self.readinprogress = True
    res = None
    try:
     buffer = self.pms._cmd("passive_read")
     res = self.pms.sensor.decode(buffer)
     self.lastread = res
    except Exception as e:
     self.readinprogress = False
    self.readinprogress = False
   return self.lastread

pms_devices = []

def request_pms_device(devtype="None",serialp=""):
  global pms_devices, pms_types
  if devtype=="None" or serialp=="":
   return None
  for i in range(len(pms_devices)):
   if (pms_devices[i].serialp == serialp):
    if (pms_devices[i].devtype != devtype) or (pms_devices[i].pms is None):
     pms_devices[i] = PMSEntity(devtype,serialp)
    return pms_devices[i]
  pms_devices.append(PMSEntity(devtype,serialp))
  return pms_devices[-1]
