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
uart = machine.UART(0, baudrate=256000, tx=machine.Pin(0), rx=machine.Pin(1))

HDR = b"\xF4\xF3\xF2\xF1"
END = b"\xF8\xF7\xF6\xF5"

STATE = {
    0x00: "no target",
    0x01: "moving",
    0x02: "stationary",
    0x03: "moving+stationary",
}

buf = bytearray()

# Tuning
MAX_CM = 100
MIN_E_MOVE = 30
MIN_E_STAT = 30
OFF_DELAY_S = 8
FAIL_TIMEOUT_S = 5

last_valid_ms = 0
last_uart_ms = time.ticks_ms()


                    #LED setup
white_led = Pin(16, Pin.OUT)
red_led = Pin(17, Pin.OUT)
blue_led = Pin(18, Pin.OUT)



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
# Helper function to combine low and high bytes
def le16(b0, b1):
    return b0 | (b1 << 8)


# MM-Wave function, returns True if occupied, False if not
def read_mmwave():
    global buf, last_valid_ms, last_uart_ms

    occupied = False

    if uart.any():
        data = uart.read()
        if data:
            buf.extend(data)
            last_uart_ms = time.ticks_ms()

    while True:
        start = buf.find(HDR)
        if start < 0:
            if len(buf) > 200:
                buf = buf[-50:]
            break

        end = buf.find(END, start)
        if end < 0:
            break

        frame = bytes(buf[start:end+4])
        buf = buf[end+4:]

        if len(frame) < 23:
            continue

        data_type = frame[6]
        head = frame[7]

        if data_type != 0x02 or head != 0xAA:
            continue

        t = frame[8:17]
        status = t[0]

        move_cm = le16(t[1], t[2])
        move_e  = t[3]
        stat_cm = le16(t[4], t[5])
        stat_e  = t[6]
        detect_cm = le16(t[7], t[8])

        if detect_cm != 0:
            dist_cm = detect_cm
        else:
            dist_cm = min(
                move_cm if move_cm > 0 else 9999,
                stat_cm if stat_cm > 0 else 9999
            )

        in_range = (dist_cm > 0) and (dist_cm <= MAX_CM)
        energy_ok = (move_e >= MIN_E_MOVE) or (stat_e >= MIN_E_STAT)

        valid = (status != 0x00) and in_range and energy_ok

        now = time.ticks_ms()
        if valid:
            last_valid_ms = now

    # off-delay latch
    now = time.ticks_ms()

    if last_valid_ms == 0:
        occupied = False
    else:
        occupied = time.ticks_diff(now, last_valid_ms) <= int(OFF_DELAY_S * 1000)

    # fail-safe: if no UART data for too long, force unoccupied
    if time.ticks_diff(time.ticks_ms(), last_uart_ms) > int(FAIL_TIMEOUT_S * 1000):
        occupied = False

    return occupied

                    #Combination of the functions to work together based on occupancy

def perfect_room():

  light_threshold = ___                #lower than this, turn light on
  temp_too_hot = 25                #higher than this, start cooling
  temp_too_cold = 20                #lower than this, start heating

  occupied = read_mmwave()
  
  white_led.value(0)
  red_led.value(0)
  blue_led.value(0)

  lux = read_light()
  tempC = read_temperature()
  
  if occupied and lux <= ___:                #If room is occupied and light is dim, turn on light, otherwise keep light off
    white_led.value(1)

  
  if occupied: 
    if tempC is not None:                #Safety check if light is reading values or not
      if tempC > temp_too_hot:                #If room is occupied and temp is hot, start cooling
        blue_led.value(1)
      elif tempC < temp_too_cold:                #If room is occupied and temp is cold, start heating
        red_led.value(1)
    
  












































































