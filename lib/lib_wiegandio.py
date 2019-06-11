#!/usr/bin/env python3
#############################################################################
############### Helper Library for Wiegand communication ####################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import wiegand_io2

class Wiegand2():
 def __init__(self):
  self.d0 = 0
  self.d1 = 0
  self.wrCapsule = wiegand_io2.construct()

 def begin(self,d0,d1):
  if self.wrCapsule:
   try:
    result = wiegand_io2.begin(self.wrCapsule,d0,d1)
    self.d0 = d0
    self.d1 = d1
   except:
    result = 0
    self.d0 = 0
  return result

 def getPins(self):
  return self.d0, self.d1

 def isinitialized(self):
  if self.wrCapsule:
   try:
    result = wiegand_io2.isinitialized(self.wrCapsule)
   except:
    result = 0
    self.d0 = 0
  return result

 def GetPendingBitCount(self):
  if self.d0 >0:
   try:
    return wiegand_io2.GetPendingBitCount(self.wrCapsule)
   except:
    return 0
  else:
   return 0

 def ReadData(self):
  if self.d0 >0:
   try:
    return wiegand_io2.ReadData(self.wrCapsule)
   except:
    return 0
  else:
   return 0

