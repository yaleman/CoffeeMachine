#!/usr/bin/python
""" Does the coffee machine magic thing! """

# documentation for GPIO inputs: http://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
# pretty pinout - http://pinout.xyz
# Pi pin map (GPIO.BCM)
# 5v | 5v | GN | 14 | 15 | 18 | GN | 23 | 24 | GN | 25 | 08 | 07
# 3v | 2  |  3 |  4 | GN | 17 | 27 | 22 | 3v | 10 |  9 | 11 | GN

# GPIO.BOARD
# 5v | 5v | GN |  8 | 10 | 12 | GN | 16 | 18 | GN | 22 | 24 | 26
# 3v | 3  |  5 |  7 | GN | 11 | 13 | 15 | 3v | 19 | 21 | 23 | GN

DEBUG = True
USE_TEMP = False
USE_HEATER = False
USE_PUMP = False
TEMP_SETPOINT = 92.0
TEMP_INTERVAL = 0.0
TEMP_UNITS = 'c'
MAX_TIME_ON = 3600
#GPIO outputs
PIN_MAIN = 11
PIN_HEATER = 13
PIN_PUMP = 15
# GPIO inputs
PIN_MAIN_BUTTON = 16
PIN_PUMP_BUTTON = 18
# MAX31855 pins
PIN_MAX_CS = 24
PIN_MAX_CLOCK = 23
PIN_MAX_DATA = 22
# GPIO Groups
PIN_OUTPUTS = {'main' : PIN_MAIN, 'heater' : PIN_HEATER, 'pump' : PIN_PUMP}
PIN_INPUTS = (PIN_MAIN_BUTTON, PIN_PUMP_BUTTON)

import sys, time
from collections import deque
try:
    #https://github.com/Tuckie/max31855
    from max31855.max31855 import MAX31855
    # requires RPi.GPIO
except ImportError:
    USE_TEMP = False
    print("Failed to import max31855")

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Failed to import RPi GPIO libraries, quitting.")
    sys.exit()

def debug(text):
    """ output a thing """
    if(DEBUG):
        print(text)

############## CoffeeMachine Class Start ##############

class CoffeeMachine(object):
    """ magical coffee state machine """
    def __init__(self):
        """ startup """
        self.current_time = time.time()

        #reset to base state, assume the machine should be on, pump off """
        self.status = {'startup_time' : time.time(),\
            'timeout' : False, 'last_power_on' : 0, 'last_tick' : time.time(),\
            'temp_lastcheck' : time.time()}
        # keep a history of temperatures, for graphing and PID
        self.temp = 0
        self.temphistory = deque([])
        # set the pin numbering to what's on the board and configure outputs
        GPIO.setmode(GPIO.BOARD)
        # configure the pins to be outputs
        debug("Setting up pins")
        for pin in PIN_OUTPUTS:
            debug("Setting pin {} as output".format(PIN_OUTPUTS[pin]))
            GPIO.setup(PIN_OUTPUTS[pin], GPIO.OUT)  # set the pins required as outputs
            self.setpin(False, pin) # set the pins to off for starters
        # configure the input pins
        for pin in PIN_INPUTS:
            debug("Setting pin {} as input".format(pin))
            GPIO.setup(pin, GPIO.IN)
        # callbacks for buttons, pin, rising/falling, callback, bouncetime
        GPIO.add_event_detect(PIN_MAIN_BUTTON, callback=self.callback_powerbutton, bouncetime=200)
        #if(USE_PUMP == True):
        GPIO.add_event_detect(PIN_PUMP_BUTTON, callback=self.callback_pumpbutton, bouncetime=200)

        if(USE_TEMP):
            # connect to the thermocouple
            self.thermocouple = MAX31855(PIN_MAX_CS, PIN_MAX_CLOCK, PIN_MAX_DATA, TEMP_UNITS)
            # force initial temp check
            self.checktemp(True)
        else:
            self.thermocouple = False
        # state machines are go!
        self.state = self.state_base

    def __del__(self):
        """ shutdown cleanup steps """
        if(USE_TEMP):
            self.thermocouple.cleanup()
        GPIO.cleanup()

    ######## BUTTON CALLBACKS ########
    def callback_powerbutton(self):
        """ handles pressing the main power button PIN_MAIN_BUTTON """
        debug("Button: POWER")
        # if the power's already on, turn off
        if(self.status['main'] == True):
            self.set_alloff()
        # if the power's off, then turn on to a base state
        else:
            self.set_base()

    def callback_pumpbutton(self):
        """ handles pressing the pump button PIN_PUMP_BUTTON """
        # if main is off, ignore pump button
        if(self.state['main'] == False):
            pass
        # if pump is on and main is on, turn the pump off
        elif(self.state['pump'] == True):
            self.status['pump'] = True
        # if pump is off and main is on, turn the pump on
        else:
            self.status['pump'] = False

    ######## STATE DEFINITIONS ########
    def state_base(self):
        """ base state """
        # main power is on, assume heater should be on, pump off
        self.handle_heater()

    def state_pumpon(self):
        """ pump is on """
        self.handle_heater()

    @staticmethod
    def state_alloff():
        """ all off """
        pass

    ######## SETTERS ########
    def setpin(self, status, pin):
        """ sets the local value and pin """
        debug("Setting pin #{} to {}".format(pin, status))
        self.status[pin] = status
        if(status == True):
            GPIO.output(PIN_OUTPUTS[pin], GPIO.HIGH)
        else:
            GPIO.output(PIN_OUTPUTS[pin], GPIO.LOW)
        time.sleep(0.01)

    def set_base(self):
        """ pump off, main on """
        self.setpin(True, 'main')
        self.setpin(False, 'pump')
        self.setpin(False, 'heater')
        self.status['timeout'] = False
        self.status['last_power_on'] = time.time()

    def set_alloff(self):
        """ everything is off, this is the "sleepy" state """
        self.setpin(False, 'main')
        self.setpin(False, 'pump')
        self.setpin(False, 'heater')
        self.status['timeout'] = True
        self.status['last_power_on'] = 0
        self.state = self.state_alloff

    ############ UTILS ################
    def handle_heater(self):
        """ deals with the heater - should it be on, what's the temp etc? """
        # double check heater should be on
        self.checktemp()
        tempdiff = TEMP_SETPOINT - self.temp

        if(self.status['main'] == True):
            if(tempdiff < 0):
                self.setpin(False, 'heater')
            else:
                self.setpin(True, 'heater')
        else:
            self.setpin(False, 'heater')

    def checktemp(self, forced=False):
        """ checks the temp, but only if it's forced or it's been long enough """
        if(USE_TEMP):
            current_time = time.time()
            if(forced or (current_time - self.status['temp_lastcheck'] > TEMP_INTERVAL)):
                print("Checking temp...")
                self.status['temp_lastcheck'] = current_time
                self.temp = self.thermocouple.get()
                print("Temperature is: {}".format(self.temp))
                self.temphistory.append(self.temp)
                if(len(self.temphistory) > 100):
                    self.temphistory.popleft()

    def tick(self):
        """ handle an instance in time """
        # update the timers
        self.current_time = time.time()
        time_since_last_tick = self.current_time - self.status['last_tick']
        # do what the state does
        debug("State: {}".format(self.state.__doc__))
        self.state()

        # handle the possibility that the system is overloaded and just die
        if(time_since_last_tick > 0.5):
            sys.exit("Program running too slow, scary things might happen")

        if(self.status['timeout'] == False):
            # check to see if the machine's been on too long
            if (self.current_time - self.status['last_power_on'] > MAX_TIME_ON):
                debug("Timeout, shutdown!")
                self.set_alloff()
                self.status['timeout'] = True
        debug("M: {} P: {} H: {}".format(self.status['main'], self.status['pump'], self.status['heater']))
        if(USE_TEMP == True):
            debug("{}".format('+'*self.temp/2+'|'))
            # I wanna use sparkcharts - https://github.com/1stvamp/py-sparkblocks.git

        # finally update the last tick time
        self.status['last_tick'] = self.current_time

############## CoffeeMachine Class End ##############

def main():
    """ main loop """
    machine = CoffeeMachine()
    while(True): # do a barrel roll!
        machine.tick()

if __name__ == '__main__':
    main()


