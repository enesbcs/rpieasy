#!/usr/bin/env python3
#############################################################################
################ Helper Library for MySQL communication #####################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import sqlite3
import time

class DB_SQLite3():

 def __init__(self):
  self.connected = False
  self.db = None
  self.cur = None
  self.datasetchanged = False
  self.writeinprogress = False

 def connect(self,dbname=None):
  self.connected = False
  if dbname is None or dbname=="":
   return False
  try:
   self.db = sqlite3.connect(database=dbname,check_same_thread=False)
   self.cur = self.db.cursor()
   self.connected = True
   self.datasetchanged = False
   self.writeinprogress = False
  except Exception as e:
   print(e)
   self.connected = False

 def disconnect(self):
  if self.connected:
   self.save(True) # commit if necessarry
   try:
    self.db.close()
   except:
    pass
  self.connected = False

 def sqlexec(self,sqlstr=""):
  succ = False
  if self.connected==False or sqlstr=="":
   return False
  st = sqlstr.strip()
  if (st[:4].lower()) in ["inse","upda","drop","crea"]:
   self.datasetchanged = True
   if self.writeinprogress:
     for i in range(0,5):
      time.sleep(0.1)
      if self.writeinprogress == False:
       break
   self.writeinprogress = True
  try:
   self.cur.execute(sqlstr)
   succ = True
   self.writeinprogress = False
  except:
   self.writeinprogress = False
   succ = False

 def sqlget(self):
  res = None
  if self.connected:
   try:
    return self.cur.fetchone()
   except:
    res = None
  return res

 def is_writeable(self):
  res = False
  if self.connected and self.writeinprogress==False:
   res = True
  return res

 def is_save_needed(self):
  return self.datasetchanged

 def save(self,WhenNeeded=False):
  if self.connected:
   if WhenNeeded:
    if self.datasetchanged==False: # if not changed pass commit
     return False
   try:
    self.db.commit()
   except:
    pass
  self.datasetchanged = False

 def create_sensortable(self):
  self.sqlexec("DROP TABLE easysensor")
  self.sqlexec("CREATE TABLE easysensor ('id' INTEGER PRIMARY KEY AUTOINCREMENT, 'time' INTEGER DEFAULT CURRENT_TIMESTAMP,'unit' INTEGER DEFAULT 0,'nodename' TEXT DEFAULT NULL,'tasknum' INTEGER,'taskname' TEXT DEFAULT NULL,'sensortype' INTEGER DEFAULT 1,'value1' REAL,'value2' REAL DEFAULT 0,'value3' REAL DEFAULT 0,'value4' REAL DEFAULT 0,'rssi' INTEGER DEFAULT 0,'battery' INTEGER DEFAULT 100,'valuetext' TEXT DEFAULT NULL)")
  self.save()

 def isexist_sensortable(self):
  self.sqlexec("SELECT count(*) FROM easysensor")
  res = self.sqlget()
  if res is None:
   res = False
  else:
   res = True
  return res

