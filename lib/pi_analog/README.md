# pi_analog Python library for using resistive sensors with a Raspberry Pi

## Installation

Run the following commands to install the library:

```
$ git clone https://github.com/simonmonk/pi_analog.git
$ cd pi_analog
$ sudo python3 setup.py install
```

If you want to use the library with python2 change _python3_ in the last coommand above into _python_.

## Hardware

The library assumes that you have the hardware setup like this:

![Schematic](https://github.com/simonmonk/pi_analog/blob/master/hardware/schematic.png?raw=true)

Which you could build on a breadboard using a photoresistor as a sensor like this:

![Breadboard](https://github.com/simonmonk/pi_analog/blob/master/hardware/breadboard.png?raw=true)

The Monk Makes Electronics Starter Kit for Raspberry Pi (https://www.monkmakes.com/rpesk2) includes all the components you need to make the example above and also includes a thermistor for temperature measurement.



## Example Usage

You will find a few examples on how to use the library in the examples folder. The simple example just displays the resistance value of the sensor every second.

```
from PiAnalog import *
import time

p = PiAnalog()

while True:
    print(p.read_resistance())
    time.sleep(1)
```


The library also includes methods for using Thermistors. So if you have a 1k thermistor with a Beta of 3800, you could use the following code to measure the temperature in degrees C.

```
from PiAnalog import *
import time

p = PiAnalog()

while True:
    print(p.read_temp_c(3800, 1000))
    time.sleep(1)
```

If you want to use different calues of C1 and R1, then you can supply them as parameters to the constructor like this:

```
p = PiAnalog(0.01, 10000)
```

The example above for a 10nF (0.01uF) capaciotor and a 10k resistor.


## How it Works

This technique relies on the ability of GPIO pins to switch between being an input and an output while the controlling program is running. The basic sequence of events in taking a measurement is as follows:

1. Make pin A an input. Make pin B an output and LOW and wait until the capacitor is discharged
2. Make a note of the time. Make pin B and input and pin A a HIGH output. C1 will now start to charge.
3. When the voltage across C1 reaches about 1.35V  it will stop being a LOW input and be measures as HIGH by the GPIO pin connected to B. The time taken for this to happen is a measurement of the resistance of the sensor and R1.
 

The code in PyAnalog.py is pretty well commented, so take a look if you are curious.

The key formula is:

T = -t / (ln(1-(Vt / Vs))

Where:
* The time constant T is also (R1 + Rsensor) * C1
* t is the time at which the voltage of C1 reaches Vt
* Vt is the voltage at which a digital input counts as HIGH on a Raspberry Pi GPIO pin (about 1.35V)
* Vs is the supply voltage for the charging pin (always 3.3V)


