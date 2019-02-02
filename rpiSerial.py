try:
 import serial
 import serial.tools.list_ports
except:
 print("pyserial not installed!")# sudo pip3 install pyserial

try:
 FIVEBITS  = serial.FIVEBITS
 SIXBITS   = serial.SIXBITS
 SEVENBITS = serial.SEVENBITS
 EIGHTBITS = serial.EIGHTBITS
 STOPBITS_ONE = serial.STOPBITS_ONE
 STOPBITS_TWO = serial.STOPBITS_TWO
 PARITY_NONE  = serial.PARITY_NONE
 PARITY_EVEN  = serial.PARITY_EVEN
 PARITY_ODD   = serial.PARITY_ODD
 PARITY_MARK  = serial.PARITY_MARK
 PARITY_SPACE = serial.PARITY_SPACE
except Exception as e:
 FIVEBITS  = 5
 SIXBITS   = 6
 SEVENBITS = 7
 STOPBITS_ONE = 1
 STOPBITS_TWO = 2
 PARITY_NONE  = 'none'
 PARITY_EVEN  = 'even'
 PARITY_ODD   = 'odd'
 PARITY_MARK  = 'mark'
 PARITY_SPACE = 'space'
 
class SerialPort:

 def __init__(self,pportname,pbaud,pbytesize=8,pparity='none',pstopbits=1,ptimeout=0):
  self.ser = None
  self.name = ""
  self.initialized = False
  try:
   self.ser = serial.Serial(pportname,pbaud,timeout=ptimeout,bytesize=pbytesize,stopbits=pstopbits)
#   self.ser = serial.Serial(pportname,pbaud,timeout=ptimeout,bytesize=pbytesize,parity=pparity,stopbits=pstopbits)
   self.initialized = True
  except Exception as e:
   print(e)
   self.initialized = False
  self.available=None
  try:
    if self.ser.inWaiting()>=0:
     self.available = self.available_old
  except:
   self.available=None
  if self.available is None:
   try: 
    if self.ser.in_waiting>=0:
     self.available = self.available_new
   except: 
    self.available=None
  self.isopened = None
  try:
   self.ser.isOpen()
   self.isopened = self.ser.isOpen
  except Exception as e:
   self.isopened = None
  if self.isopened is None:
   try:
    s = self.ser.is_open
    self.isopened = self.isopenednew
   except Exception as e:
    self.isopened = None
  if self.available is None or self.isopened is None:
   self.initialized = False
  self.name = pportname

 def available_old(self):
  return self.ser.inWaiting()

 def available_new(self):
  try:
   res = self.ser.in_waiting
  except:
   res = 0
  return res

 def isopenednew(self):
  return (self.initialized and self.ser.is_open)

 def getportname(self):
  return str(self.name)

   
# def isopened(self):
#  return self.ser.isOpen()
# def available(self):
#  return self.ser.inWaiting()
  
 def read(self,rlen=1):
  return self.ser.read(rlen)

 def readline(self):
  return self.ser.readline()

 def write(self,data):
  wb = 0
  if self.initialized:
   if type(data) is bytes:
     dsend = data
   elif type(data) is str:
     dsend = bytes(data,"utf-8")
   else:
     dsend = bytes(data)
   try:
    wb = self.ser.write(dsend)
   except:
    wb = 0
  return wb

 def __del__(self):
  if self.initialized:
   try:
    self.ser.close()
   except:
    pass

 def close(self):
  self.__del__()

def serial_portlist():
  ports = []
  for port in serial.tools.list_ports.comports():
   ports.append(str(port.device))
  return ports

UsedSerialPorts = []

#ser = SerialPort("/dev/ttyUSB0",9600)
#while 1:
#         inbuff = ser.available()
#         if inbuff > 0:
#           msgCOM = ser.read(inbuff)
#           print(msgCOM)
