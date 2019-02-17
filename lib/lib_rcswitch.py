#!/usr/bin/env python3
#############################################################################
############ Helper Library for RCSwitch RF communication ###################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import py_rcswitch

class RF():
 def __init__(self):
  self.rfCapsule = py_rcswitch.construct()

# def __del__(self):
#  try:
#   py_rcswitch.delete_object(self.rfCapsule)
#  except:
#   pass

 def initpin(self):
  if self.rfCapsule:
   try:
    result = py_rcswitch.initpin(self.rfCapsule)
   except:
    result = 0
  return result

 def isinitok(self):
  return py_rcswitch.isinitok(self.rfCapsule)

 def setProtocol(self, protocol):
  py_rcswitch.setProtocol(self.rfCapsule,protocol)

 def setPulseLength(self, pulselength):
  py_rcswitch.setPulseLength(self.rfCapsule,pulselength)

 def setRepeatTransmit(self, repeat):
  py_rcswitch.setRepeatTransmit(self.rfCapsule,repeat)

 def setReceiveTolerance(self, percent):
  py_rcswitch.setReceiveTolerance(self.rfCapsule,percent)

 def enableTransmit(self,pin):
  py_rcswitch.enableTransmit(self.rfCapsule,pin)

 def disableTransmit(self):
  py_rcswitch.disableTransmit(self.rfCapsule)

 def send_binstr(self,codeword):
  py_rcswitch.send_binstr(self.rfCapsule,str(codeword))

 def send(self,code,length):
  py_rcswitch.send(self.rfCapsule,int(code),int(length))

 def enableReceive(self,pin):
  py_rcswitch.enableReceive(self.rfCapsule,pin)

 def disableReceive(self):
  py_rcswitch.disableReceive(self.rfCapsule)

 def resetAvailable(self):
  py_rcswitch.resetAvailable(self.rfCapsule)

 def available(self):
  return py_rcswitch.available(self.rfCapsule)

 def getReceivedValue(self):
  return py_rcswitch.getReceivedValue(self.rfCapsule)

 def getReceivedBitlength(self):
  return py_rcswitch.getReceivedBitlength(self.rfCapsule)

 def getReceivedProtocol(self):
  return py_rcswitch.getReceivedProtocol(self.rfCapsule)

def getRFDev(receiver=False): #request receiver or sender device
 global RFDevices
 if receiver:
  if RFDevices[1] is None:
   RFDevices[1] = RF()
  return RFDevices[1]
 else:
  if RFDevices[0] is None:
   RFDevices[0] = RF()
  return RFDevices[0]

RFDevices = [None,None]
