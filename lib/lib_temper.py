#!/usr/bin/env python3
#############################################################################
################ Helper Library for Temper Temp+Hum devices #################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import lib.temper.temper as temper

def get_temper_list():
 global usbtemper, temperlist
 try:
  temperlist = usbtemper.read()
 except:
  temperlist = []
 return temperlist

def get_select_list():
 ul = get_temper_list()
 rl = []
 if len(ul)>0:
  for t in range(len(ul)):
   try:
    tid = int(ul[t]["busnum"])*10000+int(ul[t]["devnum"])
    tname = ul[t]["firmware"]+" ("+str(hex(int(ul[t]["vendorid"])))+":"+str(hex(int(ul[t]["productid"])))+")"
   except:
    continue
   rl.append([t,tid,tname])
 return rl

def force_temper_detect():
 global usbtemper
 try:
  if usbtemper is None:
   usbtemper = temper.Temper()
 except:
   usbtemper = temper.Temper()

usbtemper = None
temperlist = []
force_temper_detect()
