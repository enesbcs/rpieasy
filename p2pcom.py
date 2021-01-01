#!/usr/bin/env python3
#
# Simple command line program to detect ESPEasy P2P peers in network
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
from sys import exit, argv
import time
import signal
import socket
import struct

controllerport = 65501
nodelist = []
listening = False

def getunitordfromnum(unitno):
  global nodelist
  for n in range(len(nodelist)):
   if int(nodelist[n]["unitno"]) == int(unitno):
    return n
  return -1

def nodesort(item):
  v = 0
  try:
   v = int(item["unitno"])
  except:
   v = 0
  return v

class data_packet:
 buffer = bytearray(255)
 infopacket = {"mac":"","ip":"","unitno":-1,"build":0,"name":"","type":0,"port":80}
 pkgtype = 0

 def __init__(self):
  self.clear()

 def clear(self):
  self.buffer = bytearray(255)
  self.infopacket["mac"] = ""
  self.infopacket["ip"] = ""
  self.infopacket["unitno"] = -1
  self.infopacket["build"] = 0
  self.infopacket["name"] = ""
  self.infopacket["type"] = 0
  self.infopacket["port"] = 80
  self.pkgtype = 0

 def decode(self):
  tbuffer = list(self.buffer)
  self.pkgtype = 0
  if tbuffer[0] == 255:
   if tbuffer[1] == 1: # sysinfo len=80
    self.pkgtype = 1
    if len(self.buffer)>=41:
     cdata = struct.unpack_from('<B B 6B 4B B H 25s B H',self.buffer)
    else:
     cdata = struct.unpack_from('<B B 6B 4B B',self.buffer)
    array_alpha = cdata[2:8]
    self.infopacket["mac"] = ':'.join('{:02x}'.format(x) for x in array_alpha).upper()
    array_alpha = cdata[8:12]
    self.infopacket["ip"] = '.'.join(str(int(x)) for x in array_alpha)
    self.infopacket["unitno"] = int(cdata[12])
    try:
     self.infopacket["build"] = int(cdata[13])
     self.infopacket["name"] = decodezerostr(cdata[14])
     self.infopacket["type"] = int(cdata[15])
     pport = int(cdata[16])
     if pport not in [80,8008,8080]:
      pport = 80
     self.infopacket["port"] = pport
    except:
     pass

def shownodes():
   global nodelist
   if len(nodelist)>0:
    print(nodelist)

def receiver(timeout=0):
   global controllerport, nodelist, listening
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Make Socket Reusable
   s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Allow incoming broadcasts
   s.setblocking(False) # Set socket to non-blocking mode
   s.bind(('',int(controllerport)))
#   data =''
   address = ''
   starttime = time.time()
   dp = data_packet()
   while listening:
    if timeout>0:
     if (time.time()-starttime)>timeout:
      listening = False
    dp.clear()
    try:
        dp.buffer,address = s.recvfrom(10000)
    except socket.error:
        pass
    else:
        dp.decode()
        if dp.pkgtype==1:
         un = getunitordfromnum(dp.infopacket["unitno"]) # process incoming alive reports
         if un==-1:
          nodelist.append({"unitno":dp.infopacket["unitno"],"name":dp.infopacket["name"],"build":dp.infopacket["build"],"type":dp.infopacket["type"],"ip":dp.infopacket["ip"],"port":dp.infopacket["port"],"age":0})
          print("New P2P unit discovered: "+str(dp.infopacket["unitno"])+" "+str(dp.infopacket["ip"])+" "+str(dp.infopacket["mac"]))
          nodelist.sort(reverse=False,key=nodesort)
         else:
          nodelist[un]["age"] = 0
          print("Unit alive: "+str(dp.infopacket["unitno"]))
    time.sleep(0.01) # sleep to avoid 100% cpu usage
   shownodes()

def udpsender(unitno,data,retrynum=1):
  global controllerport
  destip = "255.255.255.255"
  if destip != "":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if type(data) is bytes:
     dsend = data
    elif type(data) is str:
     dsend = bytes(data,"utf-8")
    else:
     dsend = bytes(data)
    for r in range(retrynum):
      try:
#       print(dsend," ",destip," ",controllerport) # DEBUG
       s.sendto(dsend, (destip,int(controllerport)))
      except:
       pass
      if r<retrynum-1:
       time.sleep(0.1)

def signal_handler(signal, frame):
  global nodelist
  print("\n")
  shownodes()
  print("Program exiting gracefully")
  exit(0)

if __name__ == '__main__':
 signal.signal(signal.SIGINT, signal_handler)
 if len(argv)<2:
   print("Simple ESPEasy P2P peers comm program")
   print("Command line parameters:")
   print(" -L <portnum> <timeout_second>		: listen for P2P peers on network at specified UDP port (default is 65500)")
   print(" -S <portnum> <nodenum> <command>		: Send command to selected <nodenum> through <portnum> UDP port")
   exit(0)
 else:

  if argv[1].lower() == "-l": #listen mode
   try:
    controllerport = int(argv[2])
   except:
    pass
   try:
    timeout = int(argv[3])
   except:
    timeout = 0
   print("Listening for incoming UDP packets on port "+str(controllerport))
   if timeout==0:
    print("Press CTRL-C to abort...")
   listening = True
   receiver(timeout)
  elif argv[1].lower() == "-s": #send mode
   try:
    controllerport = int(argv[2])
   except:
    pass
   try:
    unitno = int(argv[3])
   except:
    unitno = 255
   try:
    command = str(argv[4])
   except:
    command = ""
   if command != "":
    print("Sending command to Unit "+str(unitno)+" through UDP port "+ str(controllerport))
    udpsender(unitno,command,1)
