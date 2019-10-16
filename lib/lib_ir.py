#!/usr/bin/env python3
#############################################################################
##################### Helper Library for LIRC IR ############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import fcntl
import time
import os
import subprocess
import array
import struct
import glob
import linux_os as OS

#sudo apt-get install ir-keytable

#lirc.h
LIRC_MODE_SCANCODE      = 0x00000008

LIRC_GET_FEATURES       = 0x80046900 # 32bit int
LIRC_GET_SEND_MODE      = 0x80046901
LIRC_GET_REC_MODE       = 0x80046902 # _IOR('i', 0x00000002, __u32)
LIRC_SET_SEND_MODE      = 0x40046911
LIRC_SET_REC_MODE       = 0x40046912
LIRC_SET_SEND_CARRIER   = 0x40046913
LIRC_SET_SEND_DUTY_CYCLE = 0x40046915

# * @timestamp: Timestamp in nanoseconds using CLOCK_MONOTONIC when IR
# *      was decoded.
# * @flags: should be 0 for transmit. When receiving scancodes,
# *      LIRC_SCANCODE_FLAG_TOGGLE or LIRC_SCANCODE_FLAG_REPEAT can be set
# *      depending on the protocol
# * @rc_proto: see enum rc_proto
# * @keycode: the translated keycode. Set to 0 for transmit.
# * @scancode: the scancode received or to be sent
# */
#struct lirc_scancode {
#        __u64   timestamp;
#        __u16   flags;
#        __u16   rc_proto;
#        __u32   keycode;
#        __u64   scancode;
#}

RC_PROTO_UNKNOWN        = 0
RC_PROTO_OTHER          = 1
RC_PROTO_RC5            = 2
RC_PROTO_RC5X_20        = 3
RC_PROTO_RC5_SZ         = 4
RC_PROTO_JVC            = 5
RC_PROTO_SONY12         = 6
RC_PROTO_SONY15         = 7
RC_PROTO_SONY20         = 8
RC_PROTO_NEC            = 9
RC_PROTO_NECX           = 10
RC_PROTO_NEC32          = 11
RC_PROTO_SANYO          = 12
RC_PROTO_MCIR2_KBD      = 13
RC_PROTO_MCIR2_MSE      = 14
RC_PROTO_RC6_0          = 15
RC_PROTO_RC6_6A_20      = 16
RC_PROTO_RC6_6A_24      = 17
RC_PROTO_RC6_6A_32      = 18
RC_PROTO_RC6_MCE        = 19
RC_PROTO_SHARP          = 20
RC_PROTO_XMP            = 21
RC_PROTO_CEC            = 22
RC_PROTO_IMON           = 23
RC_PROTO_RCMM12         = 24
RC_PROTO_RCMM24         = 25
RC_PROTO_RCMM32         = 26
RC_PROTO_XBOX_DVD       = 27

RC_PROTO = ["Unknown","Other","RC-5","RC-5_X20","RC-5_SZ","JVC","SONY_12","SONY_15","SONY_20",
"NEC","NEC_X","NEC_32","SANYO","MCIR2_KBD","MCIR2_MSE","RC-6_0","RC-6_6A_20","RC-6_6A_24","RC-6_6A_32",
"RC-6_MCE","SHARP","XMP","CEC","IMON","RCMM_12","RCMM_24","RCMM_32","XBOX_DVD"]

RC_BITLEN = [
{"name":"RC-5","len":14},
{"name":"RC-5_SZ","len":15},
{"name":"RC-5_X20","len":20},
{"name":"JVC","len":16},
{"name":"SONY_12","len":12},
{"name":"SONY_15","len":15},
{"name":"SONY_20","len":20},
{"name":"NEC","len":16},
{"name":"NEC_X","len":20},
{"name":"NEC_32","len":32},
{"name":"SANYO","len":20},
{"name":"RC-6_0","len":16},
{"name":"RC-6_6A_20","len":20},
{"name":"RC-6_6A_24","len":24},
{"name":"RC-6_6A_32","len":32},
{"name":"SHARP","len":13},
]

class IREntity():
 def __init__(self, irdevname, receiver=True, callback=None): # "/dev/lirc-rx"
  self.initialized = False
  self.espeasy_compatible = True # at least try to be...
  self.irdevname = irdevname
  self.receiver  = receiver
  self.lirc = None
  self.callback = callback
  lircdev = True
  try:
   if self.receiver:
    self.lirc = open(self.irdevname,"rb",buffering=0)
   else:
    self.lirc = open(self.irdevname,"wb+",buffering=0)
  except:
   lircdev = False
   self.lirc = None
   return
  par1 = struct.pack("i",LIRC_MODE_SCANCODE)
  try:
   if self.receiver:
    fcntl.ioctl(self.lirc,LIRC_SET_REC_MODE,par1) # try to set mode
   else:
    fcntl.ioctl(self.lirc,LIRC_SET_SEND_MODE,par1) # try to set mode
  except Exception as e:
   print("LIRC setup failed: ",str(e))
   self.lirc = None
   lircdev = False
   return
  result = array.array('h', [0])
  try:
   if self.receiver:
    if fcntl.ioctl(self.lirc, LIRC_GET_REC_MODE, result, True) == -1: # get mode
     lircdev = False
   else:
    if fcntl.ioctl(self.lirc, LIRC_GET_SEND_MODE, result, True) == -1: # get mode
     lircdev = False
  except Exception as e:
     lircdev = False
  if lircdev and result[0]==LIRC_MODE_SCANCODE:
   self.initialized = True
  else:
   self.lirc = None

 def __del__(self):
  self.stop()

 def stop(self):
  self.initialized = False

 def poller(self): # blocking reader function!!
  while self.initialized and self.receiver:
   data = self.lirc.read(24)
   if len(data)>=24:
    rdata = struct.unpack_from('<Q H H L Q',data)
    if rdata[2]>=0 and rdata[2]<28:
     protname = get_protoname(rdata[2])
     revit = False
     if self.espeasy_compatible:
      if protname[:3].lower() in ["nec","jvc","sony"]:
       revit = True
     if self.callback is None:
      print(protname,hexit(rdata[4],revit))
     else:
      self.callback(protname,hexit(rdata[4],revit))

 def setsender(self):
  try:
   self.lirc.close()  # try to force reconnect
  except:
   pass
  par1 = struct.pack("i",LIRC_MODE_SCANCODE)
  try:
    self.lirc = open(self.irdevname,"wb+",buffering=0)
    fcntl.ioctl(self.lirc,LIRC_SET_SEND_MODE,par1) # try to set mode
    par1 = struct.pack("i",38000)
    fcntl.ioctl(self.lirc,LIRC_SET_SEND_CARRIER,par1)
    par1 = struct.pack("i",50)
    fcntl.ioctl(self.lirc,LIRC_SET_SEND_DUTY_CYCLE,par1)
  except Exception as e:
   print("LIRC setup failed: ",str(e))
  time.sleep(0.2)

 def irsend(self,code,protocol=11): #default is nec32
  global RC_PROTO
  if self.initialized and self.receiver==False:
     try:
      pnum = int(protocol)
     except:
      pnum = -1
     if pnum<2 or pnum>27:
      pnum = -1
     if pnum==-1:
      try:
       pnum = RC_PROTO.index(protocol.upper())
      except:
       pnum = -1
     if pnum>-1:
      val = 0
      protname = get_protoname(pnum)
      if self.espeasy_compatible:
       if protname[:3].lower() in ["nec","jvc","sony"]:
        code = int(hexit(code,True),0)
      buffer = struct.pack("<Q H H L Q",val,val,pnum,val,code)
#      print(buffer,len(buffer)) # debug
      self.setsender()
      self.lirc.write(buffer)
      return True
     else:
      return False

def reverseBits(num,bitSize): 
     binary = bin(num)
     reverse = "0b"+binary[-1:1:-1]
     reverse = reverse + (bitSize - len(reverse)+2)*'0'
     return int(reverse,2)

def hexit(num,reverse=False):
    res = num
    if reverse:
     if num<256:
      bitnum = 8
     elif num<65535:
      bitnum = 16
     elif num<4294967295:
      bitnum = 32
     else:
      bitnum = 64
     res = str(hex(reverseBits(num,bitnum)))
     if len(res)>6:
      res = "0x"+ res[6:10] + res[2:6]
    else:
     res = str(hex(res))
    return res

def get_protoname(num):
 global RC_PROTO
 num = int(num)
 if num<0 or num>27:
  num = 0
 return RC_PROTO[num]

def find_lirc_devices():
  rlist = []
  try:
   devlist = glob.glob('/dev/lirc*')
   return devlist
  except:
   return rlist

def get_ir_supported_protocols():
 protos  = []
 cmdline = "ir-keytable"
 try:
  output = subprocess.Popen(cmdline,stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines=True)
  while output.poll() is None:
   line = output.stderr.readline()
   if line != "":
    l = line.split(":")
    if len(l)>1:
     if "Supported kernel protocols" in l[0]:
      p = l[1].split(" ")
      for i in range(len(p)):
       if p[i].strip()!="" and p[i].strip()!="\n":
        protos.append(p[i])
      break
 except:
  pass
 return protos

def get_ir_enabled_protocols():
 protos  = []
 cmdline = "ir-keytable"
 try:
  output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT, shell=True, timeout=3,universal_newlines=True)
  lines = output.splitlines()
  for line in lines:
   if line != "":
    l = line.split(":")
    if len(l)>1:
     if "Enabled kernel protocols" in l[0]:
      p = l[1].split(" ")
      for i in range(len(p)):
       if p[i].strip()!="" and p[i].strip()!="\n":
        protos.append(p[i])
      break
 except:
  pass
 return protos

def set_ir_protocols(protolist):
 protos = []
 if " " in protolist:
  protos = protolist.split(" ")
 elif "," in protolist:
  protos = protolist.split(",")
 elif type(protolist) in (tuple,list):
  protos  = protolist
 else:
  protos.append(str(protolist))
 if len(protos)<1:
  return
 cmdline = OS.cmdline_rootcorrect("sudo ir-keytable")
 for i in range(len(protos)):
  cmdline += " -p "+str(protos[i])
 try:
  output = os.popen(cmdline)
  for line in output:
   pass
 except:
  pass

def clearprotoname(protoname):
 return str(protoname).replace(" ","").replace("_","").replace("-","").upper()

def get_protonum(protoname,bitlen=8):
 global RC_PROTO
 protonames = clearprotoname(protoname)
 res = []
 for b in range(len(RC_PROTO)):
  if clearprotoname(RC_PROTO[b])==protonames:
   res.append(b)
 protonames = protonames[:3]
 pl = get_protobitlen(protoname)

 if (len(res)==1): # exact match
   if len(pl)<2:
    return res[0] # no alternatives, no check
   else:
    for bl in range(len(pl)): # check length
     if clearprotoname(protoname)==clearprotoname(pl[bl]["name"]):
       if int(bitlen)<=int(pl[bl]["len"]):
        return RC_PROTO.index(pl[bl]["name"]) # return value

 if len(res)<1:
  for b in range(len(RC_PROTO)):
   if clearprotoname(RC_PROTO[b])[:3]==protonames:
    res.append(b)
 if len(res)>0:
  if len(pl)>1:
   blfound = False
   for bl in range(len(pl)):
    if int(bitlen)<=int(pl[bl]["len"]):
     res = []
     res.append(RC_PROTO.index(pl[bl]["name"])) # return optimal value
     blfound = True
     break
   if blfound==False:
     res = []
     res.append(RC_PROTO.index(pl[-1]["name"])) # return largest one if not found optimal
 if len(res)>0:
  return res[0]
 else:
  return -1

def get_protobitlen(protoname):
 global RC_BITLEN
 protonames = clearprotoname(protoname)[:3]
 res = []
 for b in range(len(RC_BITLEN)):
  if clearprotoname(RC_BITLEN[b]["name"])[:3]==protonames:
   res.append(RC_BITLEN[b])
 return res

ir_devices = []

def request_ir_device(irname, recmode=True, cbfunc=None):
  for i in range(len(ir_devices)):
   if (ir_devices[i].irdevname == irname):
    return ir_devices[i]
  ir_devices.append(IREntity(irname, recmode, cbfunc))
  return ir_devices[-1]

