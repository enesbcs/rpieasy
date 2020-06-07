#!/usr/bin/env python3
#############################################################################
################## Telegram notifier plugin for RPIEasy #####################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import nplugin
import webserver
import rpieGlobals
import rpieTime
import misc
import commands
import threading
import json
import time
import signal
import sys
import lib.lib_dring as dring
import random

class Plugin(nplugin.NPluginProto):
 NPLUGIN_ID = 7
 NPLUGIN_NAME = "Jami (Experimental)"

 def __init__(self,nindex): # general init
  nplugin.NPluginProto.__init__(self,nindex)
  self.server = "localhost"
  self.port = 80
  self.dest = ""
  self.body=""     # template
  self.jami=None
  self.connectionmode=0

 def getuniquename(self):
  try:
   res = "jami_"+str(self.jami.account)
  except:
   res = "jami_"+str(self.dest)
  return res

 def plugin_init(self,enableplugin=None):
    nplugin.NPluginProto.plugin_init(self,enableplugin)
    self.initialized = False
    if self.enabled:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Try to init Jami connection ")
     try:
      self.sessid = self.jami.sessid
     except:
      self.sessid = -1

     jamict = self.connectionmode
     if jamict==0:
      try:
       self.jami = dring.request_dring_channel(self.getuniquename(),0,True) # create or get existing Jami handler from library
       self.initialized = self.jami.initialized
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Jami DBUS init error: "+str(e))
     else: # bridge mode
      try:
       self.jami = dring.request_dring_bridge() # create or get existing Jami handler from library
       self.initialized = self.jami.initialized
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Jami bridge init error: "+str(e))
     if self.initialized:
       if self.sessid != self.jami.sessid:
        try:
         self.jami.daemon = True          # start it if not yet started
         self.jami.start()
        except:
         pass
        if jamict==0:
         signal.signal(signal.SIGINT, self.signal_handler) # grab back signal handler, otherwise ctrl-c will not work
        misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Jami connected: "+str(self.jami.initialized and self.jami.operational))
     else: # not initialized?
      rpieTime.addsystemtimer(30,self.initcheck,[0,0])

 def initcheck(self,timerid,pararray):
     if self.initialized==False:
      self.plugin_init()

 def signal_handler(self, signal, frame): # backup handler, defined at RPIEasy.py originally
  import webserver
  import commands
  try:
   import gpios
  except Exception as e:
   pass
  commands.doCleanup()
  webserver.WebServer.stop()
  try:
   gpios.HWPorts.cleanup()
  except:
   pass
  time.sleep(1)
  print("\nProgram exiting gracefully")
  sys.exit(0)

 def webform_load(self): # create html page for settings
#  webserver.addFormTextBox("Server","server",self.server,128)
#  webserver.addFormNumericBox("Port","port",self.port,1,65535)
  choice1 = self.connectionmode
  options = ["Direct DBUS session (no root)","UDP JamiBridge (any user)"]
  optionvalues = [0,1]
  webserver.addFormSelector("Connection mode","connmode",len(optionvalues),options,optionvalues,None,choice1)
  webserver.addFormNote("Download and install Jami from <a href='https://jami.net/download/'>https://jami.net/download/</a>. Set up an account by its GUI, after that it can be monitored by RPIEasy.")
  webserver.addFormNote("Direct session can only be used if RPIEasy started with the same user as the Jami application!")
  webserver.addFormNote("JamiBridge can be used, IF the external jamibridge.py started with the same user as the Jami application! RPIEasy can be started as root in this case. The jamibridge.py can be found in the same directory as RPIEasy.py, the sample desktop entry can be found at rpieasy/lib/dringctrl/jamibridge.desktop. Please consult your distribution manual for autostarting application with your GUI.")
  if self.initialized:
   try:
    status = (self.jami.initialized and self.jami.operational)
    webserver.addHtml("<tr><td>Connected to Jami daemon<td>"+str(status)+"</tr>")
    webserver.addHtml("<tr><td>Account in use<td>"+str(self.jami.account)+"</tr>")
    cl = self.jami.getContactList()
    if len(cl)>0:
      webserver.addHtml("<tr><td>Addressee:<td>")
      webserver.addSelector_Head("destination",False)
      for i in range(len(cl)):
       webserver.addSelector_Item(cl[i],cl[i],(cl[i]==self.dest),False)
      webserver.addSelector_Foot()
   except Exception as e:
    webserver.addHtml("<tr><td>Status<td>"+str(e)+"</tr>")
  webserver.addHtml("<TR><TD>Body:<TD><textarea name='body' rows='5' cols='80' size=255 wrap='off'>")
  webserver.addHtml(str(self.body))
  webserver.addHtml("</textarea>")
  return True

 def webform_save(self,params): # process settings post reply
  par = webserver.arg("connmode",params)
  try:
   self.connectionmode = int(par)
  except:
   self.connectionmode = 0

  par = webserver.arg("destination",params)
  try:
   self.dest = str(par)
  except:
   self.dest = ""

  self.body    = webserver.arg("body",params)
  self.plugin_init()
  return True

 def notify(self,pmsg=""):
  if self.initialized==False or self.enabled==False or self.dest=="":
   return False
  if pmsg=="":
   message = self.msgparse(self.body)
  else:
   message = self.msgparse(pmsg)
  try:
       self.jami.sendText(self.dest,message)
       misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Sending Jami notification")
  except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Jami error: "+str(e))
  return True

 def msgparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
      return resstr
