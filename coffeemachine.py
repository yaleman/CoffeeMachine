#!/usr/bin/python

""" Does the coffee machine magic thing! """

# documentation for GPIO inputs: http://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/

# Pi pin map (GPIO.BCM)
# 5v | 5v | GN | 14 | 15 | 18 | GN | 23 | 24 | GN | 25 | 08 | 07
# 3v | 2  |  3 |  4 | GN | 17 | 27 | 22 | 3v | 10 |  9 | 11 | GN

# GPIO.BOARD
# 5v | 5v | GN |  8 | 10 | 12 | GN | 16 | 18 | GN | 22 | 24 | 26
# 3v | 3  |  5 |  7 | GN | 11 | 13 | 15 | 3v | 19 | 21 | 23 | GN

DEBUG = True
USE_TEMP = False
TEMP_INTERVAL = 0.5
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
PIN_OUTPUTS = (PIN_MAIN, PIN_HEATER, PIN_PUMP)
PIN_INPUTS = (PIN_MAIN_BUTTON, PIN_PUMP_BUTTON)

import sys, time
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

def setpin(pin, test):
    """ sets a pin based on a boolean test """
    debug("Setting pin #{} to {}".format(pin, test))
    if(test == True):
        GPIO.output(pin, GPIO.HIGH)
    else:
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.01)


############## CoffeeMachine Class Start ##############

class CoffeeMachine(object):
    """ magical coffee state machine """
    def __init__(self):
        """ startup """
        self.current_time = time.time()

        #reset to base state, assume the machine should be on, pump off """
        self.status = {'main' : True, 'startup_time' : time.time(),\
            'timeout' : False, 'last_power_on' : time.time(), 'last_tick' : time.time(),\
            'pump' : False, 'heater' : False, 'temp_lastcheck' : time.time()}

        # set the pin numbering to what's on the board and configure outputs
        GPIO.setmode(GPIO.BOARD)

        for pin in PIN_OUTPUTS:
            debug("Setting pin {} as output".format(pin))
            GPIO.setup(pin, GPIO.OUT)  # set the pins required as outputs
            setpin(pin, False) # set the pins to off for starters
        self.state = self.state_base
        #TODO: use this
        callback_comment_todo = """
        Threaded callbacks
RPi.GPIO runs a second thread for callback functions. This means that callback functions can be run at the 
same time as your main program, in immediate response to an edge. For example:
def my_callback(channel):
    print('This is a edge event callback function!')
    print('Edge detected on channel %s'%channel)
    print('This is run in a different thread to your main program')

GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback)  # add rising edge detection on a channel
...the rest of your program...
If you wanted more than one callback function:
def my_callback_one(channel):
    print('Callback one')

def my_callback_two(channel):
    print('Callback two')

GPIO.add_event_detect(channel, GPIO.RISING)
GPIO.add_event_callback(channel, my_callback_one)
GPIO.add_event_callback(channel, my_callback_two)
Note that in this case, the callback functions are run sequentially, not concurrently. This is because there 
is only one thread used for callbacks, in which every callback is run, in the order in which they have been defined.
"""
        del(callback_comment_todo)
        # force initial temp check
        self._checktemp(True)

        if(USE_TEMP):
            self.thermocouple = MAX31855(PIN_MAX_CS, PIN_MAX_CLOCK, PIN_MAX_DATA, TEMP_UNITS)
        else:
            self.thermocouple = False

    def __del__(self):
        """ shutdown cleanup steps """
        if(USE_TEMP):
            self.thermocouple.cleanup()
        GPIO.cleanup()

    def handle_heater(self):
        """ deals with the heater - should it be on, what's the temp etc? """
        pass

    def callback_powerbutton(self):
        """ handles pressing the main power button PIN_MAIN_BUTTON """
        pass

    def callback_pumpbutton(self):
        """ handles pressing the pump button PIN_PUMP_BUTTON """



    def state_base(self):
        """ base state, main power is on, assume heater should be on, pump off """
        self.handle_heater()

    def state_pumpon(self):
        """ pump is on """
        self.handle_heater()

    @staticmethod
    def state_alloff():
        """ doesn't need to anything """
        pass

    def set_alloff(self):
        """ everything is off, this is the "sleepy" state """
        self.status['main'] = False
        self.status['pump'] = False
        self.status['heater'] = False
        self.state = self.state_alloff

    def _checktemp(self, forced=False):
        """ checks the temp, but only if it's forced or it's been long enough """
        if(USE_TEMP):
            current_time = time.time()
            if(forced or (current_time - self.status['temp_lastcheck'] > TEMP_INTERVAL)):
                print("Checking temp...")
                self.status['temp_lastcheck'] = current_time
                self.temp = self.thermocouple.get()
                print("Temperature is: {}".format(self.temp))


    def tick(self):
        """ handle an instance in time """
        # update the timers
        self.current_time = time.time()
        time_since_last_tick = self.current_time - self.status['last_tick']
        self.state()

        # check if the user's asking me to reset
        #if(GPIO.input(PIN_MAIN_BUTTON)):
            # if the state's already on, turn everything off
            # else, reset the giblets to default
        #    pass
        # check if the pump should be on
        #elif(GPIO.input(PIN_PUMP_BUTTON)):
        #    pass
            # pump on state on
                # pump off
            # pump off or state off
                # both on

        # handle the possibility that the system is overloaded and just die
        if(time_since_last_tick > 0.5):
            sys.exit("Program running too slow, scary things might happen")

        # check to see if the machine's been on too long
        if (self.current_time - self.status['last_power_on'] > MAX_TIME_ON):
            self.set_alloff()

        setpin(PIN_MAIN, self.status['main'])
        setpin(PIN_PUMP, self.status['pump'])
        setpin(PIN_HEATER, self.status['heater'])
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


