#!/usr/bin/env python3
#############################################################################
################### Helper Library for I2C protocol #########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

import fcntl
import time

class TwoWire():

 I2C_SLAVE = 0x0703

 def __init__(self, i2c_bus_num=1,i2c_address=0):
    self.busy = False
    self.i2c_address=int(i2c_address)
    self.i2c_bus_num=-1
    self.i2cr = None
    self.iid  = -1
    self.queue = []
    self.enddelay = 0.001
    if self.i2c_address!=0:
     self.i2c_bus_num=i2c_bus_num
     self.connect()

 def connect(self):
     time.sleep(0.1)
     try:
      self.i2cr = open("/dev/i2c-"+str(self.i2c_bus_num),"rb",buffering=0)
      self.i2cw = open("/dev/i2c-"+str(self.i2c_bus_num),"wb",buffering=0)
      fcntl.ioctl(self.i2cr, self.I2C_SLAVE,self.i2c_address)
      fcntl.ioctl(self.i2cw, self.I2C_SLAVE,self.i2c_address)
     except Exception as e:
      self.i2cr = None
      self.i2c_bus_num=-1
      self.busy = False

 def setEndDelay(self,enddelay):
  self.enddelay = enddelay

 def beginTransmission(self,oid=0,queue_enabled=False): # input: oid, output: iid (iid must be used when read/write!)
   if self.busy:
    if queue_enabled:
     if oid not in self.queue:
      self.queue.append(oid)
    return 0
   elif len(self.queue)>0 and queue_enabled:
    if self.queue[0] != oid:
     if oid not in self.queue:
      self.queue.append(oid)
     return 0
    else:
     del self.queue[0]
   if self.i2cr is not None:
    self.busy = True
    self.iid  = int(str(int(time.time()))+str(oid))
    return self.iid
   else:
    self.connect()
    return 0

 def write(self, data, iid=0):
   if self.busy and self.iid==iid:
    try:
     self.i2cw.write(data)
    except:
     self.connect()

 def read(self, size, iid=0):
   buf = []
   if self.busy and self.iid==iid:
    try:
     buf = self.i2cr.read(size)
    except:
     self.connect()
   return buf

 def endTransmission(self,iid=0):
  if self.iid==iid:
   if self.busy:
    time.sleep(self.enddelay) # change to higher if error occurs!
   self.busy = False
   self.iid = -1

 def close(self):
      try:
       if self.i2cr is not None:
        self.i2cr.close()
        self.i2cw.close()
      except:
       pass

 def __del__(self):
     self.close()

 def __exit__(self, t, value, traceback):
     self.close()

i2c_connections = []

def request_i2c_device(busnum,address):
 for i in range(len(i2c_connections)):
  if ((i2c_connections[i].i2c_address == int(address)) and (i2c_connections[i].i2c_bus_num == busnum)):
   return i2c_connections[i]
 i2c_connections.append(TwoWire(busnum,address))
 return i2c_connections[-1]
