                    #imports

import machine
import time
import math
import network
import socket
from machine import Pin, ADC

                          #Sensor setups
                    #Temp setup
temp_sensor = machine.ADC(26)

Vtot = 3.3
R_FIXED = 1000    
R0 = 1000           
T0 = 298.15       
B = 3950

                    #Light setup
light_sensor = machine.ADC(27)

                    #MM-Wave setup
---------------


                    #LED setup
white_led = PIN(16, Pin.OUT)
red_led = PIN(17, Pin.OUT)
blue_led = PIN(18, Pin.OUT)



                        #Sensor Functions
                    #Temperature Function, reads voltage, translates it into resitance, then returns the temperature in Celsius
def read_temperature():
  
  raw = temp_sensor.read_u16()                #Gets the direct values
  voltage = raw * Vtot / 65535

  if voltage <= 0 or voltage >= Vtot:                #Makes sure the program does not crash if input is invalid
        return None
      
  resistance = R_FIXED * voltage / (Vtot - voltage)                #Converts values into useable temp values
  tempK = 1 / ((1/T0) + (1/B) * math.log(resistance / R0))
  tempC = tempK - 273.15

  return tempC

                    #Light Function, reads voltage, translates it into resistance, then returns the lux
def read_light():
  
  raw = light_sensor.read_u16()                #Gets the direct values
  voltage = raw * Vtot / 65535

  resistance = 1000 * voltage / (Vtot - voltage)                #Converts values into usable lux values
  lux = 500 / (resistance ** 1.4)

  return lux















































































