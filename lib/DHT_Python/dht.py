# DHT11 reader library by Zoltan Szarvas
# https://github.com/szazo/DHT11_Python
#
# Modified by Alexander Nagy 2020
#
import time
import gpios

DHT11 = 11
DHT22 = 22

def read(sensor,pin): # force to retry on fail, because DHT is a really time-sensitive device
   h = None
   c = 1
   try:
    while (h is None) and (c<7):
     h, t = raw_read(sensor,pin)
     time.sleep(0.3*c) # cooldown time
     c+=1
   except:
    h = None
    t = None
   return h, t

def raw_read(sensor,pin):
        global DHT11, DHT22
        gpios.HWPorts.setup(pin, gpios.OUT)
        # send initial high
        gpios.HWPorts.output(pin, 1)
        time.sleep(0.05)
        # pull down to low
        gpios.HWPorts.output(pin, 0)
        time.sleep(0.02)
        # change to input using pull up
        gpios.HWPorts.setup(pin, gpios.IN, gpios.PUD_UP)
        # collect data into an array
        data = __collect_input(pin)

        # parse lengths of all data pull up periods
        pull_up_lengths = __parse_data_pull_up_lengths(data)

        # if bit count mismatch, return error (4 byte data + 1 byte checksum)
        if len(pull_up_lengths) != 40:
#            print("pulluplength error")#debug
            return None, None

        # calculate bits from lengths of the pull up periods
        bits = __calculate_bits(pull_up_lengths)

        # we have the bits, calculate bytes
        the_bytes = __bits_to_bytes(bits)

        # calculate checksum and check
        checksum = __calculate_checksum(the_bytes)
        if the_bytes[4] != checksum:
#            print("checksum error")#debug
            return None, None

        if sensor==DHT22:
          temp = (the_bytes[2]*256+the_bytes[3])/10.0
          if the_bytes[2]>127:
            temp = temp - 256*256/10.
          humid = (the_bytes[0]*256+the_bytes[1])/10.0
        else:
          temp  = the_bytes[2] + float(the_bytes[3]) / 10
          humid = the_bytes[0] + float(the_bytes[1]) / 10
        # ok, we have valid data, return it
        return humid, temp

def __collect_input(pin):
        # collect the data while unchanged found
        unchanged_count = 0

        # this is used to determine where is the end of the data
        max_unchanged_count = 100

        last = -1
        data = []
        while True:
            current = gpios.HWPorts.input(pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break

        return data

def __parse_data_pull_up_lengths(data):
        STATE_INIT_PULL_DOWN = 1
        STATE_INIT_PULL_UP = 2
        STATE_DATA_FIRST_PULL_DOWN = 3
        STATE_DATA_PULL_UP = 4
        STATE_DATA_PULL_DOWN = 5

        state = STATE_INIT_PULL_DOWN

        lengths = [] # will contain the lengths of data pull up periods
        current_length = 0 # will contain the length of the previous period

        for i in range(len(data)):

            current = data[i]
            current_length += 1

            if state == STATE_INIT_PULL_DOWN:
                if current == 0:
                    # ok, we got the initial pull down
                    state = STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_INIT_PULL_UP:
                if current == 1:
                    # ok, we got the initial pull up
                    state = STATE_DATA_FIRST_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_FIRST_PULL_DOWN:
                if current == 0:
                    # we have the initial pull down, the next will be the data pull up
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_UP:
                if current == 1:
                    # data pulled up, the length of this pull up will determine whether it is 0 or 1
                    current_length = 0
                    state = STATE_DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_DOWN:
                if current == 0:
                    # pulled down, we store the length of the previous pull up period
                    lengths.append(current_length)
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue

        return lengths

def __calculate_bits(pull_up_lengths):
        # find shortest and longest period
        shortest_pull_up = 1000
        longest_pull_up = 0

        for i in range(0, len(pull_up_lengths)):
            length = pull_up_lengths[i]
            if length < shortest_pull_up:
                shortest_pull_up = length
            if length > longest_pull_up:
                longest_pull_up = length

        # use the halfway to determine whether the period it is long or short
        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []

        for i in range(0, len(pull_up_lengths)):
            bit = False
            if pull_up_lengths[i] > halfway:
                bit = True
            bits.append(bit)

        return bits

def __bits_to_bytes(bits):
        the_bytes = []
        byte = 0

        for i in range(0, len(bits)):
            byte = byte << 1
            if (bits[i]):
                byte = byte | 1
            else:
                byte = byte | 0
            if ((i + 1) % 8 == 0):
                the_bytes.append(byte)
                byte = 0

        return the_bytes

def __calculate_checksum(the_bytes):
        return the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 255
