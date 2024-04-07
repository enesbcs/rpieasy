import smbus
import time
import struct
from time import sleep

# Encoder register definition#
REG_GCONF = 0x00
REG_INTCONF = 0x01
REG_ESTATUS = 0x02
REG_CVALB4 = 0x03
REG_CVALB3 = 0x04
REG_CVALB2 = 0x05
REG_CVALB1 = 0x06
REG_CMAXB4 = 0x07
REG_CMAXB3 = 0x08
REG_CMAXB2 = 0x09
REG_CMAXB1 = 0x0A
REG_CMINB4 = 0x0B
REG_CMINB3 = 0x0C
REG_CMINB2 = 0x0D
REG_CMINB1 = 0x0E
REG_ISTEPB4 = 0x0F
REG_ISTEPB3 = 0x10
REG_ISTEPB2 = 0x11
REG_ISTEPB1 = 0x12
REG_DPPERIOD = 0x13
REG_ADDRESS = 0x14
REG_IDCODE = 0x70
REG_VERSION = 0x71
REG_I2CADDRESS = 0x72
REG_EEPROMS = 0x81

# Encoder configuration bit. Use with GCONF #
WRAP_ENABLE = 0x01
WRAP_DISABLE = 0x00
DIRE_LEFT = 0x02
DIRE_RIGHT = 0x00
IPUP_ENABLE = 0x04
IPUP_DISABLE = 0x00
RMOD_X4 = 0x10
RMOD_X2 = 0x08
RMOD_X1 = 0x00

RESET = 0x80

# Encoder status bits and setting. Use with: INTCONF for set and with ESTATUS for read the bits  #
PUSHR = 0x01
PUSHP = 0x02
PUSHD = 0x04
PUSHL = 0x08
RINC = 0x10
RDEC = 0x20
RMAX = 0x40
RMIN = 0x80


class i2cEncoderMiniLib:

    onButtonRelease = None
    onButtonPush = None
    onButtonDoublePush = None
    onButtonLongPush = None
    onIncrement = None
    onDecrement = None
    onChange = None
    onMax = None
    onMin = None
    onMinMax = None

    stat = 0
    gconf = 0

# Class costructor

    def __init__(self, bus, add):
        self.i2cbus = smbus.SMBus(bus)
        self.i2c = int(bus)
        self.i2cadd = add
        self.lock = False

# Used for initialize the encoder
    def begin(self, conf):
        self.writeEncoder8(REG_GCONF, conf & 0xFF)
        self.gconf = conf

    def reset(self) :
        self.writeEncoder8(REG_GCONF, 0x80)

# Call che attached callaback if it is defined #
    def eventCaller(self, event) :
        if event:
            event()

# Return true if the status of the encoder changed, otherwise return false #
    def updateStatus(self) :
        self.stat = self.readEncoder8(REG_ESTATUS)
        
        if (self.stat == 0):
            return False
        
        if (self.stat & PUSHR) != 0 :
            self.eventCaller (self.onButtonRelease)

        if (self.stat & PUSHP) != 0 :
            self.eventCaller (self.onButtonPush)

        if (self.stat & PUSHL) != 0 :
            self.eventCaller (self.onButtonLongPush)

        if (self.stat & PUSHD) != 0 :
            self.eventCaller (self.onButtonDoublePush)

        if (self.stat & RINC) != 0 :
            self.eventCaller (self.onIncrement)
            self.eventCaller (self.onChange)

        if (self.stat & RDEC) != 0 :
            self.eventCaller (self.onDecrement)
            self.eventCaller (self.onChange)

        if (self.stat & RMAX) != 0 :
            self.eventCaller (self.onMax)
            self.eventCaller (self.onMinMax)

        if (self.stat & RMIN) != 0 :
            self.eventCaller (self.onMin)
            self.eventCaller (self.onMinMax)

       
        return True

#********************************* Read functions ***********************************#

# Return the INT pin configuration#
    def readInterruptConfig(self) :
        return (self.readEncoder8(REG_INTCONF))

# Check if a particular status match, return true is match otherwise false. Before require updateStatus() #
    def readStatus(self, status) :
        if (self.stat & status) != 0 :
            return True
        else:
            return False

# Return the status of the encoder #
    def readStatusRaw(self) :
        return self.stat

# Return the 32 bit value of the encoder counter  #
    def readCounter32(self) :
        rv = self.readEncoder32(REG_CVALB4)
        return (rv)

# Return the 16 bit value of the encoder counter  #
    def readCounter16(self) :
        return (self.readEncoder16(REG_CVALB2))

# Return the 8 bit value of the encoder counter  #
    def readCounter8(self) :
        return (self.readEncoder8(REG_CVALB1))

# Return the Maximum threshold of the counter #
    def readMax(self) :
        return (self.readEncoder32(REG_CMAXB4))

# Return the Minimum threshold of the counter #
    def readMin(self) :
        return (self.readEncoder32(REG_CMINB4))

# Return the Steps increment #
    def readStep(self) :
        return (self.readEncoder16(REG_ISTEPB4))

# Read Double push period register #
    def readDoublePushPeriod(self) :
        return (self.readEncoder8(REG_DPPERIOD))

# Read the ID code #
    def readIDCode(self):
        return self.readEncoder8(REG_IDCODE)

# Read the Version code #
    def readVersion(self):
        return self.readEncoder8(REG_VERSION)

# Read the EEPROM memory#
    def readEEPROM(self, add):   
        return self.readEncoder8(add)

#********************************* Write functions ***********************************#
    def writeInterruptConfig(self, interrupt) :
        self.writeEncoder8(REG_INTCONF, interrupt)

# Autoconfigure the interrupt register according to the callback declared #
    def autoconfigInterrupt(self) :
        reg = 0

        if (self.onButtonRelease != None):
            reg = reg | PUSHR

        if (self.onButtonPush != None):
            reg = reg | PUSHP

        if (self.onButtonDoublePush != None):
            reg = reg | PUSHD
        
        if (self.onButtonLongPush != None):
            reg = reg | PUSHL

        if (self.onIncrement != None):
            reg = reg | RINC

        if (self.onDecrement != None):
            reg = reg | RDEC

        if (self.onChange != None):
            reg = reg | RINC
            reg = reg | RDEC

        if (self.onMax != None):
            reg = reg | RMAX

        if (self.onMin != None):
            reg = reg | RMIN

        if (self.onMinMax != None): 
            reg = reg | RMAX
            reg = reg | RMIN

        self.writeEncoder8(REG_INTCONF, reg)

# Write the counter value #
    def writeCounter(self, value) :
        self.writeEncoder32(REG_CVALB4, value)

# Write the maximum threshold value #
    def writeMax(self, max) :
        self.writeEncoder32(REG_CMAXB4, max)

# Write the minimum threshold value #
    def writeMin(self, min) :
        self.writeEncoder32(REG_CMINB4, min)

# Write the Step increment value #
    def writeStep(self, step):
        self.writeEncoder32(REG_ISTEPB4, step)

# Write Anti-bouncing period register #
    def writeDoublePushPeriod(self, dperiod):
        self.writeEncoder8(REG_DPPERIOD, dperiod)

# Write the EEPROM memory#
    def writeEEPROM(self, add, data):

        self.writeEncoder8(add, data)
        sleep(0.001)

# Send to the encoder 1 byte #
    def writeEncoder8(self, add, value):
        self.i2cbus.write_byte_data(self.i2cadd, add, value)    
        return -1

# Send to the encoder 3 byte #
    def writeEncoder24(self, add, value):
        data = [0, 0, 0, 0]
        s = struct.pack('>i', value)
        data = list(struct.unpack('BBB', s[1:4]))
        self.i2cbus.write_i2c_block_data(self.i2cadd, add, data)
        return -1
        
# Send to the encoder 4 byte #
    def writeEncoder32(self, add, value):
        data = [0, 0, 0, 0]
        s = struct.pack('>i', value)
        data = list(struct.unpack('BBBB', s))
        self.i2cbus.write_i2c_block_data(self.i2cadd, add, data)
        return -1

# read the encoder 1 byte #     
    def readEncoder8(self, add):
        data = [0]
        data[0] = self.i2cbus.read_byte_data(self.i2cadd, add)    
        value = struct.unpack(">b", bytearray(data))
        return value[0]
        
# read the encoder 2 byte #             
    def readEncoder16(self, add):
        data = [0, 0]
        data = self.i2cbus.read_i2c_block_data(self.i2cadd, add, 2)
        value = struct.unpack(">h", bytearray(data))
        return value[0] 
    
# read the encoder 4 byte #             
    def readEncoder32(self, add, ac=True):
        data = [0, 0, 0, 0]
        data = self.i2cbus.read_i2c_block_data(self.i2cadd, add, 4)
        if ac:
         if (data[0]==0 and data[1]==255 and data[1]==data[2] and data[2]==data[3]):
             raise Exception('Read error')
         if (data[0] == 128):
            data[0] = 0
        value = struct.unpack(">i", bytearray(data))
        return value[0]
