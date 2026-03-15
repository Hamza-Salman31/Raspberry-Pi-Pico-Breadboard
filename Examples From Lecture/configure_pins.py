
# Turning off and on a led pin 

import machine 
import utime

led1 = machine.Pin(16, machine.Pin.OUT) # 16 is the number on the pico and 

while True:
    led1.value(1) # value of 1 indicates 3.3 volts 
    utime.sleep(5)
    led1.value(0) # value of 0 so volateg becomes 0 turing the light off
    utime.sleep(5) 