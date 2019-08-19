#!/usr/bin/env python3
#############################################################################
################### Email notifier plugin for RPIEasy #######################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import nplugin
import webserver
import rpieGlobals
import misc
import smtplib
import commands

class Plugin(nplugin.NPluginProto):
 NPLUGIN_ID = 1
 NPLUGIN_NAME = "Email (SMTP)"

 def __init__(self,nindex): # general init
  nplugin.NPluginProto.__init__(self,nindex)
  self.server = "0.0.0.0"
  self.port = 25 #25/465
  self.security = 0 # 0:plain,1:ssl
  self.sender = ""
  self.receiver = ""
  self.login  = ""
  self.passw = ""
  self.subject ="" # template
  self.body=""     # template

 def getuniquename(self):
  return self.server

 def plugin_init(self,enableplugin=None):
  nplugin.NPluginProto.plugin_init(self,enableplugin)
  if self.passw=="*****":
   self.passw=""

 def webform_load(self): # create html page for settings
  webserver.addFormTextBox("Server","server",self.server,64)
  options = ["Plain","SSL"]
  optionvalues = [0,1]
  webserver.addFormSelector("Protocol","security",len(options),options,optionvalues,None,self.security)
  webserver.addFormNumericBox("Port","port",self.port,1,65535)
  webserver.addFormTextBox("Sender","sender",self.sender,64)
  webserver.addFormTextBox("Receiver","receiver",self.receiver,64)
  webserver.addFormTextBox("SMTP login name","login",self.login,64)
  webserver.addFormPasswordBox("STMP password","passw",self.passw,64)
  webserver.addFormTextBox("Subject","subject",self.subject,64)
  webserver.addHtml("<TR><TD>Body:<TD><textarea name='body' rows='5' cols='80' size=512 wrap='off'>")
  webserver.addHtml(str(self.body))
  webserver.addHtml("</textarea>")
  return True

 def webform_save(self,params): # process settings post reply
  self.server = webserver.arg("server",params)
  par1 = webserver.arg("security",params)
  try:
   par1=int(par1)
  except:
   par1=0
  if par1<0 or par1>1:
   par1=0
  self.security=par1
  par1 = webserver.arg("port",params)
  try:
   par1=int(par1)
  except:
   par1=25
  if par1<1 or par1>65534:
   par1=25
  self.port=par1
  self.sender   = webserver.arg("sender",params)
  self.receiver = webserver.arg("receiver",params)
  self.login    = webserver.arg("login",params)
  passw = webserver.arg("passw",params)
  if "**" not in passw:
   self.passw = passw
  self.subject = webserver.arg("subject",params)
  self.body    = webserver.arg("body",params)
  return True

 def notify(self,pmsg=""):
  if self.initialized==False or self.enabled==False:
   return False
  if self.sender=="" or self.receiver=="":
   return False
  message = ("From: %s\r\nTo: %s\r\n" % (self.sender,self.receiver))
  message += "Content-Type: text/plain; charset=utf-8\r\n"
  message += "Subject: "+self.mailparse(self.subject)+"\r\n\r\n"
  if pmsg=="":
   message += self.mailparse(self.body)
  else:
   message += self.mailparse(pmsg)
  if self.server=="0.0.0.0" or self.server=="":
   return False
  try:
   if self.security==0:
    smtpObj = smtplib.SMTP(self.server, self.port)
   elif self.security==1:
    smtpObj = smtplib.SMTP_SSL(self.server, port=self.port, timeout=2)
   if self.login!="" and self.passw!="":
    smtpObj.login(self.login,self.passw)
   smtpObj.sendmail(self.sender, self.receiver, message.encode("utf8"))
   smtpObj.quit()
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Mail sent!")
   return True
  except Exception as e:
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   return False

 def mailparse(self,ostr):
      cl, st = commands.parseruleline(ostr)
      if st=="CMD":
          resstr=str(cl)
      else:
          resstr=str(ostr)
      return resstr
