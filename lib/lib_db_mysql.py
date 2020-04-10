#!/usr/bin/env python3
#############################################################################
################ Helper Library for MySQL communication #####################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import pymysql

class DB_MySQL():

 def __init__(self):
  self.connected = False
  self.db = None
  self.cur = None
  self.datasetchanged = False
  self.writeinprogress = False
  self.dbname = ""

 def connect(self,hostname=None,dbname=None,username=None,passw=None,dbport=0):
  self.connected = False
  if dbname is None or dbname=="":
   return False
  if hostname is None or hostname=="":
   hostname = "localhost"
  if dbname is None or dbname=="":
   dbname = "easydata"
  self.dbname = dbname
  tc = 0
  try:
   self.db = pymysql.connect(host=hostname,user=username,password=passw,db=dbname,charset="utf8mb4")
   self.cur = self.db.cursor()
   self.connected = True
   self.datasetchanged = False
  except:
   tc = 1
  if tc==1:
   try:
    if int(dbport)>0:
     self.db = pymysql.connect(host=hostname,user=username,password=passw,charset="utf8mb4",port=int(dbport))
    else:
     self.db = pymysql.connect(host=hostname,user=username,password=passw,charset="utf8mb4")
    self.cur = self.db.cursor()
    self.cur.execute("CREATE DATABASE IF NOT EXISTS "+self.dbname+" CHARACTER SET utf8mb4;")
    self.cur.execute("USE "+self.dbname+";")
    self.connected = True
    self.datasetchanged = False
   except Exception as e:
    tc = 2
    print(e)
    self.connected = False

 def disconnect(self):
  if self.connected:
   self.save(True)
   try:
    self.db.close()
   except:
    pass
  self.connected = False

 def sqlexec(self,sqlstr=""):
  succ = False
  if self.connected==False or sqlstr=="":
   return False
  if self.datasetchanged==False:
   st = sqlstr.strip()
   if (st[:4].lower()) in ["inse","upda","drop","crea"]:
    self.datasetchanged = True
  try:
   self.cur.execute(sqlstr)
   succ = True
  except:
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
  return self.connected

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
  self.sqlexec("CREATE TABLE easysensor (`id` INT NOT NULL AUTO_INCREMENT,`time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,`unit` TINYINT UNSIGNED DEFAULT 0,`nodename` VARCHAR(30) DEFAULT NULL,`tasknum` SMALLINT,`taskname` VARCHAR(30) DEFAULT NULL,`sensortype` SMALLINT DEFAULT 1,`value1` FLOAT,`value2` FLOAT DEFAULT 0,`value3` FLOAT DEFAULT 0,`value4` FLOAT DEFAULT 0,`rssi` SMALLINT default 0,`battery` SMALLINT default 100,`valuetext` VARCHAR(50) DEFAULT NULL, PRIMARY KEY (`id`));")
  self.save()

 def isexist_sensortable(self):
  self.sqlexec("SELECT count(*) FROM easysensor")
  res = self.sqlget()
  if res is None:
   res = False
  else:
   res = True
  return res

