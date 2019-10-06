#!/usr/bin/env python3
#############################################################################
#################### Helper Library for MCP23017 ## #########################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
try:
 import lib.MCP230XX.MCP230XX as MCP
except:
 raise("Unable to load MCP230XX library")
import gpios
import misc
import rpieGlobals
import Settings

class MCPEntity(MCP.MCP230XX):

 def __init__(self,chip, i2cAddress, busnum=1):
  MCP.MCP230XX.__init__(self,chip,i2cAddress,busnum)
  self.externalintsetted = False
  self.extinta = 0

 def setexternalint(self,itype,intpin):
  if itype == 0:
#   if int(intpin)>-1 and int(intpin)!=self.extinta:
   if int(intpin)>-1:
    if self.extinta>-1:
     try:
      gpios.HWPorts.remove_event_detect(self.extinta)
     except:
      pass
    ptype = ""
    for b in range(len(Settings.Pinout)):
     if str(Settings.Pinout[b]["BCM"])==str(intpin):
      if Settings.Pinout[b]["actualstate"] in [0,1,2]: # input needs activehigh
       ptype="activehigh"
       etype=gpios.RISING
      elif Settings.Pinout[b]["actualstate"]==3: # input pullup needs activelow
       ptype="activelow"
       etype=gpios.FALLING
      break
    if ptype!="":
     try:
      self.interrupt_options(outputType=ptype, bankControl='both') # activelow, opendrain, activehigh
      self.extinta = int(intpin)
      gpios.HWPorts.add_event_detect(self.extinta,etype,self.callbackBoth)
      self.externalintsetted = True
     except Exception as e:
      self.externalintsetted = False
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Adding MCP interrupt failed "+str(e))
    else:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"You have failed to select a valid input Pin!")

 def __del__(self):
    # remove event handler
    if self.extinta>0:
     try:
      gpios.HWPorts.remove_event_detect(self.extinta)
     except:
      pass
    try:
     if MCP.MCP230XX is not None:
      MCP.MCP230XX.__del__(self)
    except:
     pass

mcp_devices = []

def request_mcp_device(mbusnum,mportnum,chipname="MCP23017"):
 i2caddress, realpin = get_pin_address(mportnum)
 if realpin > -1:
  for i in range(len(mcp_devices)):
   if (mcp_devices[i].i2cAddress == int(i2caddress)):
    return mcp_devices[i]
  mcp_devices.append(MCPEntity(chipname,i2caddress, busnum=mbusnum))
  return mcp_devices[-1]
 else:
  return None

def get_pin_address(pinnumber):
 number = int(pinnumber)
 ia=0
 pn=-1
 if number>0 and number<129:
  ia, pn = divmod(number,16)
  if pn==0:
   ia-=1
   pn=15
  else:
   pn-=1
  ia+=0x20
 return ia, pn

