#!/usr/bin/env python3
#############################################################################
####################### DringCtrl plugin for RPIEasy ########################
#############################################################################
#
# The Jami has to be installed and an account has to be setted up, before using this plugin!
#
# Basic operations supported such as:
#   - Firing rule condition/parameter on incoming call
#     with called ID
#   - Receiving text messages
#   - Starting a call
#   - Sending text message to peer
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import threading
import time
import signal
import sys
import lib.lib_dring as dring
import random

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 523
 PLUGIN_NAME = "Communication - Jami DringCtrl (EXPERIMENTAL)"
 PLUGIN_VALUENAME1 = "State"
 PLUGIN_VALUENAME2 = "Status"
 PLUGIN_VALUENAME3 = "Peer"
 PLUGIN_VALUENAME4 = "Text"

 def __init__(self,taskindex): # general init
   plugin.PluginProto.__init__(self,taskindex)
   self.dtype = rpieGlobals.DEVICE_TYPE_DUMMY
   self.vtype = rpieGlobals.SENSOR_TYPE_QUAD
   self.readinprogress = 0
   self.valuecount = 4
   self.senddataoption = True
   self.recdataoption = False
   self.timeroption = False
   self.timeroptional = True
   self.formulaoption = False
   self.jami = None
   self.lastinit = 0

 def plugin_init(self,enableplugin=None):
    plugin.PluginProto.plugin_init(self,enableplugin)
    self.initialized = False
    if self.enabled:
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Try to init Jami connection ")
     try:
      self.sessid = self.jami.sessid
     except:
      self.sessid = -1

     jamict = self.taskdevicepluginconfig[0]
     if jamict==0:
      try:
       self.jami = dring.request_dring_channel(self.gettaskname(),0,True) # create or get existing Jami handler from library
       self.jami.cb_ring2 = self.cb_ring2
       self.jami.cb_call = self.cb_call
       self.jami.cb_text = self.cb_text
       self.initialized = self.jami.initialized
      except Exception as e:
       misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Jami DBUS init error: "+str(e))
     else: # bridge mode
      try:
       self.jami = dring.request_dring_bridge() # create or get existing Jami handler from library
       self.jami.cb_ring2 = self.cb_ring2
       self.jami.cb_call = self.cb_call
       self.jami.cb_text = self.cb_text
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
        self.set_value(1,0,False)
        self.set_value(2,"INACTIVE",False)
        self.set_value(3,0,False)
        self.set_value(4,"",False)
        misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Jami connected: "+str(self.jami.initialized and self.jami.operational))
     else: # not initialized?
      rpieTime.addsystemtimer(30,self.initcheck,[0,0])

 def initcheck(self,timerid,pararray):
     if self.initialized==False:
      self.plugin_init()

 def plugin_exit(self):
     try:
      self.jami.stopThread() # try to stop thread at exit
     except:
      pass

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

 def call(self,target): # make a call to an adresse (video? audio?)
  ae = "-1"
  clist = self.jami.getContactList()
  if str(target).isnumeric():       # either by order
   target = int(target)
   if target < len(clist):
    ae = clist[target]
  else:
   if target in clist:              # or by direct ID
    ae = target
  if ae != "-1":
   self.jami.makeCall(str(ae)) # make the call, use default account
  else:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Jami addressee not in contact list "+str(target))

 def cb_ring2(self, stateid, statestr, caller=None):
     if (int(self.uservar[0]) != stateid) and (stateid != 0):
      self.set_value(1,stateid)
      self.set_value(2,statestr)
      self.set_value(3,caller)
      if str(self.uservar[3]) !="":
       self.set_value(4,"")
      self.plugin_senddata()
     elif int(self.uservar[0]) in [1,2] and stateid==0:
      self.set_value(1,0)
      self.set_value(2,"INACTIVE")
      if str(self.uservar[3]) !="":
       self.set_value(4,"")
      self.plugin_senddata()
     return True

 def cb_call(self, state):
#     print(state)
     if int(state)==1:
      self.set_value(1,3,False)
      self.set_value(2,"ACTIVE",False)
      if str(self.uservar[3]) !="":
       self.set_value(4,"")
      self.plugin_senddata()
     elif int(self.uservar[0]) in [1,3]:
      self.set_value(1,0,False)
      self.set_value(2,"INACTIVE",False)
      if str(self.uservar[3]) !="":
       self.set_value(4,"")
      self.plugin_senddata()
     return True

 def cb_text(self, fromacc, text):
#     print(fromacc,text)
     self.set_value(1,10,False)
     self.set_value(2,"MSG",False)
     self.set_value(3,fromacc,False)
     self.set_value(4,text,False)
     self.plugin_senddata()
     return True

 def webform_load(self):
  choice1 = self.taskdevicepluginconfig[0]
  options = ["Direct DBUS session (no root)","UDP JamiBridge (any user)"]
  optionvalues = [0,1]
  webserver.addFormSelector("Connection mode","p523_mode",len(optionvalues),options,optionvalues,None,choice1)
  webserver.addFormNote("Download and install Jami from <a href='https://jami.net/download/'>https://jami.net/download/</a>. Set up an account by its GUI, after that it can be monitored by RPIEasy.")
  webserver.addFormNote("Direct session can only be used if RPIEasy started with the same user as the Jami application!")
  webserver.addFormNote("JamiBridge can be used, IF the external jamibridge.py started with the same user as the Jami application! RPIEasy can be started as root in this case. The jamibridge.py can be found in the same directory as RPIEasy.py, the sample desktop entry can be found at rpieasy/lib/dringctrl/jamibridge.desktop. Please consult your distribution manual for autostarting application with your GUI.")
  if self.initialized:
   try:
    status = (self.jami.initialized and self.jami.operational)
    webserver.addHtml("<tr><td>Connected to Jami daemon<td>"+str(status)+"</tr>")
    webserver.addHtml("<tr><td>Account in use<td>"+str(self.jami.account)+"</tr>")
    webserver.addHtml("<tr><td>Approved contacts<td>")
    cl = self.jami.getContactList()
    for i in range(len(cl)):
     webserver.addHtml(str(cl[i])+"<BR>")
    webserver.addHtml("</tr>")
   except Exception as e:
    webserver.addHtml("<tr><td>Status<td>"+str(e)+"</tr>")
  return True

 def webform_save(self,params):
  pval = self.taskdevicepluginconfig[0]
  par = webserver.arg("p523_mode",params)
  try:
   self.taskdevicepluginconfig[0] = int(par)
  except:
   self.taskdevicepluginconfig[0] = 0
  try:
   if pval != self.taskdevicepluginconfig[0]:
    self.plugin_init()
  except:
   pass
  return True

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "jami":
   if self.initialized:
    subcmd = str(cmdarr[1].strip()).lower()
    if subcmd=="call":
     try:
      target = cmdarr[2].strip()
      self.jami.makeCall(target)
     except Exception as e:
      print(e)
    elif subcmd=="sendtext":
     try:
      target = cmdarr[2].strip()
      msg = cmdarr[3].strip()
      self.jami.sendText(target,msg)
     except Exception as e:
      print(e)
    elif subcmd=="accept":
     try:
      self.jami.acceptIncoming()
     except Exception as e:
      print(e)
    elif subcmd=="refuse":
     try:
      self.jami.refuseIncoming()
     except Exception as e:
      print(e)
    elif subcmd=="endcall":
     try:
      self.jami.endCall()
     except Exception as e:
      print(e)

    res = True
   else:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Jami is not initialized")
  return res

