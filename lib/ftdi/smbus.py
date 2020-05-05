import gpios

class SMBus:

 def __init__(self,busnum):
   self.busnum = busnum
   try:
    self.bus = gpios.HWPorts.get_i2c_ctrl(busnum)
   except:
    self.bus = None
    
 def write_quick(self,addr):
     pass # not supported

 def read_byte(self,addr):
     try:
      i2c = self.bus.get_port(addr)
      res = i2c.read(1)
     except:
      res = None
     return res

 def write_byte(self,addr,val):
     try:
      i2c = self.bus.get_port(addr)
      i2c.write(val)
     except:
      pass

 def read_byte_data(self,addr,cmd):
     try:
      i2c = self.bus.get_port(addr)
      res = i2c.read_from(int(cmd),readlen=1)
     except:
      res = None
     return res

 def write_byte_data(self,addr,cmd,val):
     try:
      i2c = self.bus.get_port(addr)
      i2c.write_to(int(cmd),val)
     except:
      pass

 def read_word_data(self,addr,cmd):
     try:
      i2c = self.bus.get_port(addr)
      res = i2c.read_from(int(cmd),readlen=2)
     except:
      res = None
     return res

 def write_word_data(self,addr,cmd,val):
     try:
      i2c = self.bus.get_port(addr)
      i2c.write_to(int(cmd),val)
     except:
      pass

 def read_block_data(self,addr,cmd,dlen=0):
     try:
      i2c = self.bus.get_port(addr)
      res = i2c.read_from(int(cmd),readlen=dlen)
     except:
      res = None
     return res

 def read_i2c_block_data(self,addr,cmd,dlen=0):
     self.read_block_data(addr,cmd,dlen)

 def write_block_data(self,addr,cmd,vals):
     try:
      i2c = self.bus.get_port(addr)
      i2c.write_to(int(cmd),vals)
     except:
      pass

 def write_i2c_block_data(self,addr,cmd,vals):
     self.write_block_data(addr,cmd,vals)
