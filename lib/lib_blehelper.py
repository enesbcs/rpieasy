#!/usr/bin/env python3
#############################################################################
###################### Helper Library for BLE ###############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import os

def find_hci_devices():
  resarr = []
  try:
   output = os.popen('hcitool dev | grep hci')
   for line in output:
    if "hci" in line:
     res = line.strip().split()
     resarr.append(res[0])
  except:
   pass
  resarr.append("hci1") #DEBUG ONLY!!!
  return resarr

class BLEStatusSemaphore():
 scanprogress = False
 requests = []
 dataflow = []
 requestimmediatestopscan = None

 def __init__(self):
  self.scanprogress = False
  self.requests = []
  self.dataflow = []
  self.requestimmediatestopscan = None

 def reportscan(self,status):     # called by scanner program
  if int(status)==0:
   if self.scanprogress==True:
    self.scanprogress = False
    self.requests = []
  else:
   self.scanprogress = True

 def norequesters(self):         # called by scanner program
  if len(self.requests)==0:
   return True
  else:
   return False

 def nodataflows(self):          # called by scanner program
  if len(self.dataflow)==0:
   return True
  else:
   return False

 def isscaninprogress(self):            # called by standard ble plugin
  return self.scanprogress

 def forcestopscan(self):
  if (self.requestimmediatestopscan is not None) and self.scanprogress:
   try:
    self.requestimmediatestopscan()
   except:
    pass

 def requeststopscan(self,tskid):        # called by standard ble plugin
  if self.scanprogress == False:
   return True
  if not (int(tskid) in self.requests):
   self.requests.append(int(tskid))

 def registerdataprogress(self,tskid):   # called by standard ble plugin
  if not (int(tskid) in self.dataflow):
   self.dataflow.append(int(tskid))

 def unregisterdataprogress(self,tskid): # called by standard ble plugin
  if (int(tskid) in self.dataflow):
   try:
    self.dataflow.remove(int(tskid))
   except:
    pass

def blestatusinit():
 global BLEStatus
 BLEStatus = []
 if len(BLEStatus)<1:
  BLEStatus.append(BLEStatusSemaphore()) # dev0
  BLEStatus.append(BLEStatusSemaphore()) # dev1
  BLEStatus.append(BLEStatusSemaphore()) # dev2
  BLEStatus.append(BLEStatusSemaphore()) # dev3

try:
 if BLEStatus is None:
  blestatusinit()
except:
  blestatusinit()

