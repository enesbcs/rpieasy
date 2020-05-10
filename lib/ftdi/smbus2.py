import gpios
import sys

class SMBus:

 def open(self):
  pass
  
 def close(self):
  pass

 def __init__(self,busnum):
   self.busnum = busnum
   try:
    self.bus = gpios.HWPorts.get_i2c_ctrl(busnum)
   except:
    self.bus = None

 def write_quick(self,addr):
     try:
      i2c = self.bus.get_port(addr)
      i2c.write([])
     except:
      pass

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

 def i2c_rdwr(self,datas):
     self.write_block_data(datas[0],datas[1][0],datas[1][1:])

class i2c_msg():
    @staticmethod
    def write(address, buf):
        """
        Prepares an i2c write transaction.
        :param address: Slave address.
        :type address: int
        :param buf: Bytes to write. Either list of values or str.
        :type buf: list
        :return: New :py:class:`i2c_msg` instance for write operation.
        :rtype: :py:class:`i2c_msg`
        """
        if sys.version_info.major >= 3:
            if type(buf) is str:
                buf = bytes(map(ord, buf))
            else:
                buf = bytes(buf)
        else:
            if type(buf) is not str:
                buf = ''.join([chr(x) for x in buf])
        return address, buf
