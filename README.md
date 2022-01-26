⚠️ THIS IS ARCHIVED AND WILL NOT BE UPDATED ⚠️

To be honest, I never even ran it live. Weird.

# CoffeeMachine

A simple implementation of a state machine designed to run a coffee machine. :)

## Features

### Implemented

 * Main power on/off with a timeout in case it's left on.
 * Two input buttons - power and pump
 * Simple temperature sensing and heater on/off based on setpoint (*UNTESTED*)
 
### Planned

 * Timed pump control - x second shot
 * PID heater temperature control
 * Remote interface/control
 
## Requirements
 
 * A [Raspberry PI](http://raspberrypi.org)
 * Solid state relays (pump, heater control)
 * A K-type thermocouple and MAX31855 SPI interface (temperature sensing)
 * A couple of SPST momentary switches
 * Wire
 * A respect for high voltage AC
 
# Warranty
 
There's no warranty implied or otherwise in the provided instructions, use at your own risk. 
