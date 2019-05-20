#!/usr/bin/env python3

# Class to control the 28BJY-48 stepper motor with ULN2003 control board.
# Converted from work done by Stephen Phillips (www.scphillips.com)

from time import sleep
import gpios

class Motor:
    def __init__(self, pins, revs_per_minute): # only output pins please, there are no checks...

        self.P1 = pins[0]
        self.P2 = pins[1]
        self.P3 = pins[2]
        self.P4 = pins[3]

        self.deg_per_step = 5.625 / 64
        self.steps_per_rev = int(360 / self.deg_per_step)  # 4096
        self.step_angle = 0  # Assume the way it is pointing is zero degrees
        self.step_angle2 = 0  # Assume the way it is pointing is zero degrees
        self.setspeed(revs_per_minute)
        self.stop()

    def setspeed(self,rpm):
        self._rpm = rpm
        # T is the amount of time to stop between signals
        self._T = (60.0 / self._rpm) / self.steps_per_rev
   
    def stop(self): 
        gpios.HWPorts.output(self.P1, 0)
        gpios.HWPorts.output(self.P2, 0)
        gpios.HWPorts.output(self.P3, 0)
        gpios.HWPorts.output(self.P4, 0)
        self.moving = False

    def move_to(self, angle):
        """Take the shortest route to a particular angle (degrees)."""
        # Make sure there is a 1:1 mapping between angle and stepper angle
        target_step_angle = 8 * (int(angle / self.deg_per_step) / 8)
        steps = target_step_angle - self.step_angle2
        steps = int(steps % self.steps_per_rev)
        if steps > self.steps_per_rev / 2:
            steps -= int(self.steps_per_rev)
#            print("moving " + str(steps) + " steps")
            self._move_acw(-steps / 8)
        else:
#            print("moving " + str(steps) + " steps")
            self._move_cw(steps / 8)
        self.step_angle = angle
        self.step_angle2 = target_step_angle
#        print("tsa",target_step_angle," steps",steps," angle ",angle," step_angle ",self.step_angle)

    def move_acw(self, angle):
        target_step_angle = (int(angle / self.deg_per_step) / 8)
        steps = target_step_angle
        steps = int(steps % self.steps_per_rev)
        self._move_acw(steps)
        self.step_angle = self.step_angle - angle
        self.step_angle2 = self.step_angle2 - target_step_angle
#        print("tsa",target_step_angle," steps",steps," angle ",angle," step_angle ",self.step_angle)

    def move_cw(self, angle):
        target_step_angle = (int(angle / self.deg_per_step) / 8)
        steps = target_step_angle
        steps = int(steps % self.steps_per_rev)
        self._move_cw(steps)
        self.step_angle = self.step_angle + angle
        self.step_angle2 = self.step_angle2 + target_step_angle
#        print("tsa",target_step_angle," steps",steps," angle ",angle," step_angle ",self.step_angle)

    def _move_cw(self, big_steps):
        self.stop()
        big_steps = int(big_steps)
        self.moving = True
        for i in range(big_steps):
            gpios.HWPorts.output(self.P4, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P2, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P3, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P1, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P2, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P4, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P1, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P3, 0)
            sleep(self._T)
            if not self.moving:
             break
        self.moving = False
 
    def _move_acw(self, big_steps):
        self.stop()
        big_steps = int(big_steps)
        self.moving = True
        for i in range(big_steps):
            gpios.HWPorts.output(self.P3, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P1, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P4, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P2, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P1, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P3, 1)
            sleep(self._T)
            gpios.HWPorts.output(self.P2, 0)
            sleep(self._T)
            gpios.HWPorts.output(self.P4, 1)
            sleep(self._T)
            if not self.moving:
             break
        self.moving = False
