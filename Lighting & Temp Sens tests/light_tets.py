from machine import Pin
import time

blue_led = Pin(18, Pin.OUT)  # GP 18 pin 24
red_led = Pin(17, Pin.OUT)   # GP 17 pin 22
white_led = Pin(16, Pin.OUT) #GP 16  pin 21

while True:
    print("teting lights")
    blue_led.value(1)   # ON
    time.sleep(1)
    
    blue_led.value(0)   # OFF
    time.sleep(1)

    red_led.value(1)   # ON
    time.sleep(1)
    
    red_led.value(0)   # OFF
    time.sleep(1)

    white_led.value(1)   # ON 
    time.sleep(1)
    
    white_led.value(0)   # OFF
    time.sleep(1)
