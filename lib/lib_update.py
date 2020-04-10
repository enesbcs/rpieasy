#!/usr/bin/env python3
#############################################################################
#################### Helper Library for Update ##############################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

import os
import signal
import linux_os as OS
import rpieGlobals
import misc
import time
import Settings

def upgrade_rpi():
  if len(Settings.UpdateString)>0:
   if Settings.UpdateString[0]=="!":
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Update in progress")
    return False
  succ = True
  ustr = "Downloading RPIEasy update from Github"
  Settings.UpdateString = "!"+ustr
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
  try:
   os.popen("cp -rf run.sh run.sh.bak && rm -rf update && git clone https://github.com/enesbcs/rpieasy.git update").read()
   time.sleep(1)
  except:
   succ = False
  if succ and os.path.isdir("update"):
   ustr = "Download successful, starting to overwrite files"
   Settings.UpdateString = "!"+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
   try:
    os.popen("rm -rf .git && rm -rf update/data update/files && mv -f update/.git .git && cp -rf update/lib/* lib/ && cp -rf update/img/* img/ && rm -rf update/lib update/img && mv -f update/* . && rm -rf update && cp -rf run.sh.bak run.sh").read()
   except:
    succ = False
   if succ:
    ustr = "Update successful"
    Settings.UpdateString = "="+ustr
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
    time.sleep(0.5)
    os.kill(os.getpid(), signal.SIGINT)
    return True
  else:
   succ = False
  if succ == False:
   ustr = "Update failed"
   Settings.UpdateString = "="+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,ustr)
  return False

def update_pip():
  if len(Settings.UpdateString)>0:
   if Settings.UpdateString[0]=="!":
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Update in progress")
    return False
  ustr = "Getting upgradable pip package list"
  Settings.UpdateString = "!"+ustr
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
  htm = "<form method='post' action='/update' enctype='multipart/form-data'>"
  htm += "<center><input type='hidden' name='mode' value='pipupgrade'><input type='submit' value='Upgrade selected'><table>"
  pnum = 0
  try:
     output = os.popen(OS.cmdline_rootcorrect('sudo -H pip3 list --outdated --format columns'))
     for line in output:
      lc = line.split()
      valid = False
      if len(lc)==4:
       try:
        if int(lc[1][0])>=0:
         valid = True
       except:
        pass
      if valid:
       htm += "<tr><td><input type='checkbox' name='p_"+str(pnum)+"' value='"+lc[0]+"' checked>"+lc[0]+"<td>"+lc[1]+"<td>"+lc[2]+"<td>"+lc[3]+"</tr>"
       pnum += 1
     if pnum==0:
       htm += "<tr><td><input type='checkbox' name='p_pip' value='pip' checked>pip<td>Either everything is up to date or outdated parameter failed<td><td></tr>"
     Settings.UpdateString = htm + "</table></center></form>"
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"pip upgrade list ready")
     return True
  except Exception as e:
   ustr = "PIP update failed "+str(e)
   Settings.UpdateString = "="+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,ustr)
  return False

def upgrade_pip(pkgs):
  if len(Settings.UpdateString)>0:
   if Settings.UpdateString[0]=="!":
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Update in progress")
    return False
  if len(pkgs)<1:
   return False
  sf = 0
  us = 0
  for p in pkgs:
   ustr = "Upgrading package "+str(p)
   Settings.UpdateString = "!"+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
   try:
     output = os.popen(OS.cmdline_rootcorrect('sudo -H pip3 install --upgrade '+str(p)))
     for line in output:
      pass
     sf += 1
   except:
     us += 1
  ustr = "PIP upgrade ended (successful:"+str(sf)+",unsuccesful:"+str(us)+")"
  Settings.UpdateString = "="+ustr
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
  return True

def update_apt():
  if len(Settings.UpdateString)>0:
   if Settings.UpdateString[0]=="!":
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Update in progress")
    return False
  ustr = "Getting fresh apt package list"
  Settings.UpdateString = "!"+ustr
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
  try:
     output = os.popen(OS.cmdline_rootcorrect('sudo apt update'))
     for line in output:
      pass
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"apt update list ready")
  except Exception as e:
   ustr = "ATP update failed "+str(e)
   Settings.UpdateString = "="+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,ustr)

  ustr = "Getting upgradable apt package list"
  Settings.UpdateString = "!"+ustr
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)

  htm = "<form method='post' action='/update' enctype='multipart/form-data'>"
  htm += "<center><input type='hidden' name='mode' value='aptupgrade'><input type='submit' value='Upgrade All'><br>Upgradable packages:<p><textarea readonly rows='20' wrap='on'>"
  try:
     output = os.popen(OS.cmdline_rootcorrect('sudo apt list --upgradable'))
     for line in output:
      htm += str(line)
     Settings.UpdateString = htm + "</textarea></center></form>"
     misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"apt upgrade list ready")
     return True
  except Exception as e:
   ustr = "APT update failed "+str(e)
   Settings.UpdateString = "="+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,ustr)
  return False

def upgrade_apt():
  if len(Settings.UpdateString)>0:
   if Settings.UpdateString[0]=="!":
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"Update in progress")
    return False
  ustr = "Upgrading APT packages<br>Please do not interrupt!"
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
  ustr += "<p style='font-weight:normal;font-size:12px;text-align:left'>"
  Settings.UpdateString = "!"+ustr
  try:
     output = os.popen(OS.cmdline_rootcorrect('sudo apt upgrade -y'))
     for line in output:
      if len(Settings.UpdateString)>2000:
       Settings.UpdateString = "!"+ustr
      Settings.UpdateString += line + "<br>"
  except Exception as e:
   ustr = "APT upgrade failed "+str(e)
   Settings.UpdateString = "="+ustr
   misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,ustr)
   return False
  ustr = "APT upgrade ended"
  Settings.UpdateString = "="+ustr
  misc.addLog(rpieGlobals.LOG_LEVEL_INFO,ustr)
  return True
