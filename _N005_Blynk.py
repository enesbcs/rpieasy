#!/usr/bin/env python3
#############################################################################
################### Blynk notifier plugin for RPIEasy #######################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import nplugin
import webserver
import rpieGlobals
import misc
import commands
import blynklib # sudo pip3 install blynklib
import lib.lib_blynk as BLYNK
import time

class Plugin(nplugin.NPluginProto):
 NPLUGIN_ID = 5
 NPLUGIN_NAME = "Blynk"

 def __init__(self,nindex): # general init
  nplugin.NPluginProto.__init__(self,nindex)
  self.server = "blynk-cloud.com"
  self.port = 80
  self.passw = ""
  self.body=""     # template

 def getuniquename(self):
  return self.server

 def plugin_init(self,enableplugin=None):
  nplugin.NPluginProto.plugin_init(self,enableplugin)
  if self.passw=="*****":
   self.passw=""

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Server","server",self.server,128)
  webserver.addFormNumericBox("Port","port",self.port,1,65535)
  webserver.addFormPasswordBox("Token","passw",self.passw,64)
  webserver.addHtml("<TR><TD>Body:<TD><textarea name='body' rows='5' cols='80' size=255 wrap='off'>")
  webserver.addHtml(str(self.body))
  webserver.addHtml("</textarea>")
  return True

 def webform_save(self,params): # process settings post reply
  self.server = webserver.arg("server",params)
  par1 = webserver.arg("port",params)
  try:
   par1=int(par1)
  except:
   par1=80
  if par1<1 or par1>65534:
   par1=80
  self.port=par1
  passw = webserver.arg("passw",params)
  if "**" not in passw:
   self.passw = passw
  self.body    = webserver.arg("body",params)
  return True

 def notify(self,pmsg=""):
  if self.initialized==False or self.enabled==False:
   return False
  if pmsg=="":
   message = self.msgparse(self.body)
  else:
   message = self.msgparse(pmsg)
  if self.server=="0.0.0.0" or self.server=="":
   return False
  connected = False
  try:
   if BLYNK.blynk.connected(): #.is_server_alive():
    connected = True
  except:
   pass
  if connected==False:
   try:
      BLYNK.blynk = blynklib.Blynk(self.passw,server=self.server,port=int(self.port),heartbeat=15)
      BLYNK.blynk.connect()
   except:
      pass
  try:
   tc = 5
   while tc>0:
    if BLYNK.blynkconnected:
     BLYNK.blynk.notify(message)
     BLYNK.blynk.run()
     tc = 0
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Blynk notify sent!")
     return True
    time.sleep(1)
    tc -= 1
   return False
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   return False

 def msgparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
      return resstr
