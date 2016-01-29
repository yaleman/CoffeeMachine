# Web interface

## Graphing

 * http://www.flotcharts.org could be handy

# doing more than one thing at once

https://docs.python.org/2/library/multiprocessing.html

# Documentation for GPIO inputs

* http://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/

# Pretty Pinout - http://pinout.xyz

    # Pi pin map (GPIO.BCM)
    # 5v | 5v | GN | 14 | 15 | 18 | GN | 23 | 24 | GN | 25 | 08 | 07
    # 3v | 2  |  3 |  4 | GN | 17 | 27 | 22 | 3v | 10 |  9 | 11 | GN

    # GPIO.BOARD
    # 5v | 5v | GN |  8 | 10 | 12 | GN | 16 | 18 | GN | 22 | 24 | 26
    # 3v | 3  |  5 |  7 | GN | 11 | 13 | 15 | 3v | 19 | 21 | 23 | GN


# Circuit diagram of GPIO buttons

The thing I forgot in my original design was to have TWO resistors instead of just one. Weird. Instead I just used the built-in inputs - but this is here for posterity and to remind me in future!

http://www.falstad.com/circuit/circuitjs.html?cct=$+1+0.000005+2.803162489452614+72+5+43%0Ar+64+208+176+128+0+10%0AR+64+208+64+272+0+0+40+3.3+0+0+0.5%0As+176+128+368+128+0+1+true%0As+176+304+368+304+0+1+true%0A162+176+128+176+64+1+2.2+1+0+0%0A162+176+304+176+368+1+2.2+1+0+0%0Ag+176+368+176+416+0%0Ag+176+64+176+32+0%0Ag+448+208+496+208+0%0Aw+448+208+368+304+0%0Aw+448+208+368+128+0%0Ax+190+86+226+89+0+12+GPIO1%0Ax+189+337+225+340+0+12+GPIO2%0Ar+64+208+176+304+0+10%0A

Basically

            ---GND
            |
            GPIO
            |
            /-+____/ ___
    3.3v -+             +-|- GND
            \-+____/ ---
            |
            GPIO
            |
            ---GND
Though this is WAY easier to sort by using BCM2 and BCM3 (Pins 3/5) which have pullup resistors. 