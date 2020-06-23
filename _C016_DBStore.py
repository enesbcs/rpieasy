#!/usr/bin/env python3
#############################################################################
##################### DBStore Controller for RPIEasy ########################
#############################################################################
#
# Sqlite and Mysql data storage backend.
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import controller
import rpieGlobals
import misc
import webserver
import datetime
import Settings
import os_os as OS
import time

_lastRSSIval = 0
_lastRSSItime = 0

backends = []
try:
 import lib.lib_db_sqlite as DBSQLITE
 backends.append("SQLite")
except:
 pass
try:
 import lib.lib_db_mysql as DBMYSQL
 backends.append("MySQL")
except:
 pass

def getCachedRSSI(urssi=-1):
 global _lastRSSIval, _lastRSSItime 
 rssi = urssi
 if ((time.time()-_lastRSSItime)>=3) and (urssi==-1):
  _lastRSSIval = OS.get_rssi()
  _lastRSSItime = time.time()
 try: 
  if urssi != -1:
   rssi = urssi
  else:
   rssi = int(_lastRSSIval)
 except:
  pass
 return str(rssi)

class Controller(controller.ControllerProto):
 CONTROLLER_ID = 16
 CONTROLLER_NAME = "DB Data Storage"

 def __init__(self,controllerindex):
  controller.ControllerProto.__init__(self,controllerindex)
  self.usesID = False
  self.usesAccount = False
  self.usesPassword = False
  self.timer30s = True
  self.db = None
  self.provider = -1
  self.connected = False
  self.dbname = ""

 def controller_init(self,enablecontroller=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  if self.enabled:
   if self.connect():
    self.initialized = True
  else:
   self.disconnect()
   self.initialized = False
  return True

 def connect(self):
  self.connected = False
  if self.provider==0:
   try:
    if self.dbname != "":
     self.db = DBSQLITE.DB_SQLite3()
     self.db.connect(self.dbname)
     if self.db.isexist_sensortable() == False:
      self.db.create_sensortable()
     self.connected = True
   except:
    self.connected = False
  elif self.provider==1:
   try:
    if self.dbname != "":
     self.db = DBMYSQL.DB_MySQL()
     if self.controllerport==0:
      self.controllerport=3306
     self.db.connect(hostname=self.controllerip,dbport=self.controllerport,dbname=self.dbname,username=self.controlleruser,passw=self.controllerpassword)
     if self.db.isexist_sensortable() == False:
      self.db.create_sensortable()
     self.connected = True
   except Exception as e:
    print(e)
    self.connected = False
  return self.connected

 def disconnect(self):
  try:
   if self.db is not None:
    self.db.disconnect()
  except:
   pass

 def webform_load(self):
  global backends
  if self.provider==0:
   webserver.addFormNote("Server address and port is not used.")
   self.controllerport=1
   self.controllerip="localhost"
   self.usesAccount = False
   self.usesPassword = False
  elif self.provider==1:
   self.usesAccount = True
   self.usesPassword = True
   if self.controllerport in [0,1,80]:
    self.controllerport=3306
  try:
   options = backends
   optionvalues = [0,1]
   webserver.addFormSelector("DB Type","c016_type",len(options),options,optionvalues,None,int(self.provider),reloadonchange=True)
  except:
   pass
  webserver.addFormTextBox("Database name","c016_dbname",str(self.dbname),255)
  return True

 def webform_save(self,params):
  try:
   self.provider = int(webserver.arg("c016_type",params))
  except:
   self.provider = 0
  try:
   self.dbname = str(webserver.arg("c016_dbname",params))
  except:
   self.dbname = ""
  return True

 def senddata(self,idx,sensortype,value,userssi=-1,usebattery=-1,tasknum=-1,changedvalue=-1):
  if self.enabled:
    sqlstr = "insert into easysensor (time,unit,nodename,taskname,sensortype"
    sqlstr2 = ") values ('"+ str(datetime.datetime.now()) +"',"+str(Settings.Settings["Unit"])+",'"+str(Settings.Settings["Name"])+"','"+str(Settings.Tasks[tasknum].gettaskname())+"',"+str(sensortype)
    vcount = 4
    if tasknum!=-1:
     try:
      sqlstr += ",tasknum"
      sqlstr2 += ","+str(tasknum+1)
      vcount = Settings.Tasks[tasknum].valuecount
     except:
      pass
    if vcount>0:
     if sensortype==rpieGlobals.SENSOR_TYPE_TEXT:
      sqlstr += ",valuetext"
     else:
      sqlstr += ",value1"
     sqlstr2 += ","+str(value[0])
    if vcount>1:
     sqlstr += ",value2"
     sqlstr2 += ","+str(value[1])
    if vcount>2:
     sqlstr += ",value3"
     sqlstr2 += ","+str(value[2])
    if vcount>3:
     sqlstr += ",value4"
     sqlstr2 += ","+str(value[3])

    sqlstr += ",rssi"
    sqlstr2 += ","+str(getCachedRSSI(userssi))
    try:
     usebattery = float(usebattery)
    except:
     usebattery = -1
    if usebattery != -1 and usebattery != 255: # battery input 0..100%, 255 means not supported
     sqlstr += ",battery"
     sqlstr2 += ","+str(usebattery)
    else:
     bval = misc.get_battery_value()
     if bval != 255:
      sqlstr += ",battery"
      sqlstr2 += ","+str(bval)

    sqlstr = sqlstr + sqlstr2+")"
#    print(sqlstr)
    try:
     self.db.sqlexec(sqlstr)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"DBStore: "+str(e))

 def timer_thirty_second(self):
  if self.initialized and self.enabled:
   try:
    self.db.save(True) # commit only if needed
   except:
    pass
  return self.timer30s
