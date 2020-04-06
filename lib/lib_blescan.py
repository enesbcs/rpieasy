#!/usr/bin/env python3
#############################################################################
################### Helper Library for BLE Scanner ##########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

from bluepy.btle import Scanner
import time

class BLEScan():
 bledev = 0
 timeout = 5.0
 scanner = None
 devices = []
 devrssi = []
 lastscan = 0

 def __init__(self,devnum=0,timeout=5.0):
  self.bledev = int(devnum)
  self.timeout = float(timeout)
  self.scanner = None
  self.devices = []
  self.devrssi = []
  self.lastscan = 0

 def stop(self):
    try:
     if self.scanner is not None:
      self.scanner.stop()
    except:
     pass

 def scan(self):
    result = False
    devices = []
    try:
     self.scanner = Scanner(self.bledev)
     devices = self.scanner.scan(self.timeout)
     result = True
     self.lastscan = time.time()
    except Exception as e:
     print("BLE error: ",e)
     self.devices = []
     self.devrssi = []
    tempdev = []
    temprssi = []
    for dev in devices:
      try:
       if self.bledev == int(dev.iface):
        temprssi.append(dev.rssi)
        tempdev.append(str(dev.addr).lower().strip())
      except:
        pass
    self.devices = tempdev
    self.devrrsi = temprssi
    return result

 def isdevonline(self,devaddress):
  return (self.getdevrssi(devaddress) != -100)

 def getdevrssi(self,devaddress):
   try:
    for d in range(len(self.devices)):
     if str(devaddress).lower().strip()==str(self.devices[d]).lower().strip():
      return self.devrrsi[d]
    return -100
   except Exception as e:
    return -100

 def getage(self):
  if self.lastscan==0:
   return -1
  try:
   result = time.time()-self.lastscan
  except:
   result = -1
  return result

blescan_devices = []

def request_blescan_device(rdevnum=0,rtimeout=5.0):
 for i in range(len(blescan_devices)):
  try:
   if ( int(blescan_devices[i].bledev) == int(rdevnum) ):
    return blescan_devices[i]
  except:
   pass
 blescan_devices.append(BLEScan(rdevnum,rtimeout))
 return blescan_devices[-1]
