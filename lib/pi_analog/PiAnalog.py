import RPi.GPIO as GPIO
import time, math

class PiAnalog:

    a_pin = 18
    b_pin = 23
    C = 0.0
    R1 = 0.0
    Vt = 0.0
    Vs = 0.0
    T5 = 0.0

    def __init__(self, C=0.33, R1=1000.0, Vt = 1.35, Vs = 3.3, a_pin=18, b_pin=23, gpioinit=True):
        if gpioinit:
         GPIO.setmode(GPIO.BCM)
         GPIO.setwarnings(False)
        self.C = C
        self.R1 = R1
        self.Vt = Vt
        self.Vs = Vs
        self.T5 = (C * R1 * 5) / 1000000.0
        self.a_pin = a_pin
        self.b_pin = b_pin

    # empty the capacitor ready to start filling it up
    def discharge(self):
        GPIO.setup(self.a_pin, GPIO.IN)
        GPIO.setup(self.b_pin, GPIO.OUT)
        GPIO.output(self.b_pin, False)
        time.sleep(self.T5) # 5T for 99% discharge

    # return the time taken for the voltage on the capacitor to count as a digital input HIGH
    def charge_time(self):
        GPIO.setup(self.b_pin, GPIO.IN)
        GPIO.setup(self.a_pin, GPIO.OUT)
        GPIO.output(self.a_pin, True)
        status_counter = 1
        t1 = time.time()
        while not GPIO.input(self.b_pin):
          if status_counter<10000:            # failsafe if no resistors connected
            status_counter += 1
          else:
            break
        t2 = time.time()
        return (t2 - t1) * 1000000 # microseconds

    # Take an analog reading as the time taken to charge after first discharging the capacitor
    def analog_read(self):
        self.discharge()
        t = self.charge_time()
        self.discharge()
        return t

    # Convert the time taken to charge the cpacitor into a value of resistance
    # To reduce errors in timing, do it a few times and take the median value.
    def read_resistance(self):
        n = 7
        readings = []
        for i in range(0, n):
            reading = self.analog_read()
            readings.append(reading)
            readings.sort()
        t = readings[int(n / 2)]
        T = -t / math.log(1.0 - (self.Vt / self.Vs))
        RC = T
        r = (RC / self.C) - self.R1
        return r

    def read_temp_c(self, B=3800.0, R0=1000.0):
        R = self.read_resistance()
        t0 = 273.15     # 0 deg C in K
        t25 = t0 + 25.0 # 25 deg C in K
        # Steinhart-Hart equation - Google it
        inv_T = 1/t25 + 1/B * math.log(R/R0)
        T = (1/inv_T - t0)
        return T
