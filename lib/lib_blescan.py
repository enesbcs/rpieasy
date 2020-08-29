#!/usr/bin/env python3
#############################################################################
################### Helper Library for BLE Scanner ##########################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

from bluepy.btle import Scanner, DefaultDelegate
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
  self._scanning = False

 def stop(self):
    try:
     if self.scanner is not None:
      self.scanner.stop()
    except:
     pass
    self._scanning = False

 def scan(self):
    result = False
    devices = []
    self._scanning = True
    try:
     self.scanner = Scanner(self.bledev)
     devices = self.scanner.scan(self.timeout)
     result = True
     self.lastscan = time.time()
    except Exception as e:
     print("BLE error: ",e)
     self.devices = []
     self.devrssi = []
    self._scanning = False
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

 def sniff(self, callback):
    self._scanning = True
    try:
     self.scanner = Scanner(self.bledev).withDelegate(SniffDelegate(callback))
     if self.timeout==0:
      while self._scanning:
       self.scanner.clear()
       self.scanner.start(passive=True)
       self.scanner.process(10)
       self.scanner.stop()
     else:
      self.scanner.scan(self.timeout,passive=True)
     self.lastscan = time.time()
    except Exception as e:
     pass
    self._scanning = False

class SniffDelegate(DefaultDelegate):
 def __init__(self, cb):
     DefaultDelegate.__init__(self)
     self.cb = cb

 def handleDiscovery(self ,dev, isnewdev, isnewdata):
     try:
      self.cb(dev, dev.getScanData())
     except Exception as e:
      print(e)

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
