#!/usr/bin/env python3
#############################################################################
###################### P2P Encoder/Decoder library ##########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import struct
import rpieGlobals

class data_packet:
 buffer = bytearray(255)
 infopacket = {"unitno":-1,"mac":"","build":0,"name":"","type":0,"cap":0}
 sensordata = {"sunit":0,"dunit":0,"pluginid":0,"idx":0,"valuecount":0,"values":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}
 cmdpacket  = {"sunit":0,"dunit":0,"cmdline":""}
 pktlen  = 0
 pkgtype = 0

 def __init__(self):
  self.clear()

 def clear(self):
  self.buffer = bytearray(255)
  self.infopacket["mac"] = ""
  self.infopacket["unitno"] = -1
  self.infopacket["build"] = 0
  self.infopacket["name"] = ""
  self.infopacket["type"] = 0
  self.sensordata["sunit"] = 0
  self.sensordata["dunit"] = 0
  self.pkgtype = 0

 def encode(self,ptype):
  self.pkgtype = ptype

  if ptype == 1:
   tbuf = [255,1]
   tbuf.append(int(self.infopacket["unitno"]))
   tbuf.append(0) # destination is broadcast
   ta = self.infopacket["mac"].split(":")
   for m in ta:
    try:
     tbuf.append(int(m,16))
    except:
     tbuf.append(0)
   tbuf.append(int(self.infopacket["build"]%256))
   tbuf.append(int(self.infopacket["build"]/256))
   tbuf.append(int(self.infopacket["type"]))
   tbuf.append(int(self.infopacket["cap"]))
   nl = len(self.infopacket["name"])
   if nl>24:
    nl = 24
   tbuf.append(int(nl)) # add string len
   for s in range(nl):
    tbuf.append(ord(self.infopacket["name"][s]))
   self.buffer = bytes(tbuf)

  if ptype == 5:
   tbuf = [255,5]
   tbuf.append(int(self.sensordata["sunit"]))
   tbuf.append(int(self.sensordata["dunit"]))
   tbuf.append(int(self.sensordata["pluginid"]%256))
   tbuf.append(int(self.sensordata["pluginid"]/256))
   tbuf.append(int(self.sensordata["idx"]%256))
   tbuf.append(int(self.sensordata["idx"]/256))
   tbuf.append(0) # samplesetcount
   nlen = int(self.sensordata["valuecount"])
   tbuf.append(nlen)
   for v in range(nlen):
    try:
     val = float(self.sensordata["values"][v])
     cvf = list(struct.pack("<f",val))# convert float to bytearray
    except:
     if type(self.sensordata["values"][v]) is str:
      cvf = self.sensordata["values"][v][0:4]   # strip string if needed
     else:
      cvf = list(self.sensordata["values"][v])  # do anything that we can..
    cl = len(cvf)
    if cl>4:
     cl = 4
    for c in range(cl):
     tbuf.append(cvf[c])
   self.buffer = bytes(tbuf)

  if ptype in [7,8]:
   tbuf = [255,int(ptype)]
   tbuf.append(int(self.cmdpacket["sunit"]))
   tbuf.append(int(self.cmdpacket["dunit"]))
   nl = len(self.cmdpacket["cmdline"])
   tbuf.append(int(nl)) # add string len
   for s in range(nl):
    tbuf.append(ord(self.cmdpacket["cmdline"][s]))
   self.buffer = bytes(tbuf)

 def decode(self):
  tbuffer = list(self.buffer)
  self.pkgtype = 0
  self.pktlen  = 0
  if len(tbuffer)<7:
   return False
  if tbuffer[0] == 255:
   if tbuffer[1] == 1:
    self.pkgtype = 1
    nlen = int(tbuffer[14])
    if nlen>len(tbuffer)-15:
     nlen = len(tbuffer)-15
    try:
     cdata = struct.unpack_from('<B B B B 6B H B B B '+str(nlen)+'s',self.buffer)
    except Exception as e:
     print(e)
    self.pktlen = 15+int(nlen)
    self.infopacket["unitno"] = int(cdata[2])
    array_alpha = cdata[4:10]
#    print(array_alpha)
    self.infopacket["mac"] = ':'.join('{:02x}'.format(x) for x in array_alpha).upper()
    try:
     self.infopacket["build"] = int(cdata[10])
     self.infopacket["type"] = int(cdata[11])
     self.infopacket["cap"] = int(cdata[12])
     self.infopacket["name"] = decodezerostr(cdata[14])
    except Exception as e:
     print(str(e))
   elif tbuffer[1] == 5:
    self.pkgtype = 5
    nlen = int(tbuffer[9])
    if nlen>len(tbuffer)-10:
     nlen = int((len(tbuffer)-10)/4)
    explen = 10+(nlen*4)
    correction = 0
    if explen+2==len(tbuffer):
     correction = 1
     try:
      cdata = struct.unpack_from('<4B 2H 2B H '+str(nlen)+'f',self.buffer)
     except Exception as e:
      print(e)
     self.pktlen = 12+(int(nlen)*4)
    else:
     try:
      cdata = struct.unpack_from('<4B 2H 2B '+str(nlen)+'f',self.buffer)
     except Exception as e:
      print(e)
     self.pktlen = 10+(int(nlen)*4)
    self.sensordata["sunit"] = int(cdata[2])
    self.sensordata["dunit"] = int(cdata[3])
    self.sensordata["pluginid"]  = int(cdata[4])
    self.sensordata["idx"]   = int(cdata[5])
    self.sensordata["values"] = []
    if rpieGlobals.VARS_PER_TASK<nlen:
     nlen = rpieGlobals.VARS_PER_TASK
    self.sensordata["valuecount"] = nlen
    for f in range(nlen):
     try:
      self.sensordata["values"].append(float(cdata[8+f+correction]))
     except:
      pass
   elif tbuffer[1] in [7,8]:
    self.pkgtype = int(tbuffer[1])
#    print(self.buffer)
    nlen = int(tbuffer[4])
    if nlen>len(tbuffer)-5:
     nlen = len(tbuffer)-5
    try:
     cdata = struct.unpack_from('<5B '+str(nlen)+'s',self.buffer)
    except Exception as e:
     print(e)
    self.pktlen = 5+int(nlen)
    self.cmdpacket["sunit"] = int(cdata[2])
    self.cmdpacket["dunit"] = int(cdata[3])
    self.cmdpacket["cmdline"] = decodezerostr(cdata[5])
   else:
    print("Not supported frame type: "+str(tbuffer[1]))

# Helper functions

def decodezerostr(barr):
 result = ""
 b=len(barr)
 for b in range(len(barr)):
  if barr[b] == 0:
   try:
    result = barr[:b].decode("utf-8")
   except:
    result = str(barr[:b])
   break
 if b>=len(barr)-1:
   try:
    result = barr.decode("utf-8")
   except:
    result = str(barr)
 return result.strip()
