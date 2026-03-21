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


                    #MM-Wave Function
-=-=-=-=-=-=-=-=-=-=-=-=-=

                    #Combination of the functions to work together based on occupancy

def perfect_room():

  light_threshold = ___                #lower than this, turn light on
  temp_too_hot = 25                #higher than this, start cooling
  temp_too_cold = 20                #lower than this, start heating

  white_led.value(0)
  red_led.value(0)
  blue_led.value(0)

  lux = read_light()
  tempC = read_temperature()
  
  if occupied and lux <= ___:                #If room is occupied and light is dim, turn on light, otherwise keep light off
    white_led.value(1)
  else:
    white_led.value(0)

  
  if occupied 
    if tempC is not None:                #Safety check if light is reading values or not
      if tempC > temp_too_hot:                #If room is occupied and temp is hot, start cooling
        blue_led.value(1)
      elif tempC < temp_too_cold:                #If room is occupied and temp is cold, start heating
        red_led.value(1)
    
  












































































