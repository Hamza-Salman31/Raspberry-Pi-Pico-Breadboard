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

  motionStatus = "DETECTED" if occupied else "NONE"                #Status strings for website
  motionClass = "detected" if occupied else "none"

  whiteStatus = "ON" if white_led.value() else "OFF"                #Status strings for website
  whiteClass = "on" if white_led.value() else "off"

  blueStatus = "ON" if blue_led.value() else "OFF"                #Status strings for website
  blueClass = "on" if blue_led.value() else "off"

  redStatus = "ON" if red_led.value() else "OFF"                #Status strings for website
  redClass = "on" if red_led.value() else "off"
    
  return (tempC, lux, motionStatus, motionClass, whiteStatus, whiteClass, blueStatus, blueClass, redStatus, redClass)


# ── WIFI ACCESS POINT ──────────────────────────────────
ssid     = 'GROUP_3'          # TODO: change to whatever you want (also we can add this anywhere we want when we implement it)
password = 'onetwothreefourfive67'  # TODO: change to whatever you want (min 8 chars)

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)

while ap.active() == False:
    pass

print('Access point active!')
print('IP address:', ap.ifconfig()[0])  # almost always 192.168.4.1, but it should print it if we need to

# ── SOCKET SERVER ──────────────────────────────────────
s = socket.socket()
s.bind(('', 80))
s.listen(5)

# ── MAIN LOOP ──────────────────────────────────────────
while True:
    conn, addr = s.accept()
    request = conn.recv(1024)
    request = str(request)

    response = web_page("22.4", "315", "DETECTED", "detected", "ON", "on", "OFF", "off", "OFF", "off", "AUTOMATIC")
    conn.send("HTTP/1.1 200 OK\n")
    conn.send("Content-Type: text/html\n")
    conn.send("Connection: close\n\n")
    conn.sendall(response)
    conn.close()



def web_page(tempValue, lightValue,
             motionStatus, motionClass,
             whiteLedStatus, whiteLedClass,
             redLedStatus, redLedClass,
             blueLedStatus, blueLedClass,
             modeStatus):

    if tempValue is not None and tempValue >= 25:
        # TODO: change 25 if you want a different high-temp alert threshold
        alertStyle = "display:block"
        tempBadge  = "HOT"
        tempClass  = "hot"
    else:
        alertStyle = "display:none"
        tempBadge  = "NORMAL"
        tempClass  = "normal"

    tempDisplay = str(tempValue) if tempValue is not None else "ERR"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Smart Room Control</title>
  <meta http-equiv="refresh" content="5">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background: #003B5C; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 4px; color: white; }}
    p.sub {{ color: #cce5ff; font-size: 0.85rem; margin-top: 0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }}
    .card {{ background: white; border-radius: 8px; padding: 14px 16px; border: 1px solid #ddd; }}
    .card h3 {{ font-size: 0.75rem; text-transform: uppercase; color: #999; margin: 0 0 10px 0; letter-spacing: 0.08em; }}
    .value {{ font-size: 1.8rem; font-weight: bold; color: #222; }}
    .unit {{ font-size: 0.9rem; color: #888; }}
    .status-row {{ display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; }}
    .status-row:last-child {{ border-bottom: none; }}
    .label {{ color: #666; }}
    .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
    .on       {{ background: #d4edda; color: #155724; }}
    .off      {{ background: #f8d7da; color: #721c24; }}
    .detected {{ background: #cce5ff; color: #004085; }}
    .none     {{ background: #e2e3e5; color: #383d41; }}
    .hot      {{ background: #f8d7da; color: #721c24; }}
    .normal   {{ background: #d4edda; color: #155724; }}
    .btn-row  {{ display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }}
    .btn {{ padding: 8px 14px; border: none; border-radius: 5px; font-size: 0.82rem; cursor: pointer; text-decoration: none; font-family: Arial, sans-serif; }}
    .btn-green {{ background: #28a745; color: white; }}
    .btn-red   {{ background: #dc3545; color: white; }}
    .btn-blue  {{ background: #007bff; color: white; }}
    .btn-grey  {{ background: #6c757d; color: white; }}
    .full      {{ grid-column: 1 / -1; }}
    .alert {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; font-size: 0.88rem; }}
  </style>
</head>
<body>

  <!-- TODO: change "Smart Room Energy Management" to whatever you want the page title to say -->
  <h1>Smart Room Energy Management</h1>

  <!-- TODO: update group/section info if needed -->
  <p class="sub">Group 3 &mdash; B02 &nbsp;|&nbsp; Raspberry Pi Pico W &nbsp;|&nbsp; Auto-refresh: 5s</p>

  <!-- high temp alert banner — shows automatically when temp >= 25 -->
  <div class="alert" style="{alertStyle}">
    High temperature detected! HVAC cooling activated.
  </div>

  <div class="grid">

    <!-- TEMPERATURE CARD -->
    <div class="card">
      <!-- TODO: update GP26 if your temp sensor is on a different pin -->
      <h3>Temperature &middot; GP26</h3>
      <!-- tempDisplay is the number from read_temperature(), or "ERR" if sensor fails -->
      <div class="value">{tempDisplay} <span class="unit">&deg;C</span></div>
      <div class="status-row" style="margin-top:8px">
        <span class="label">Status</span>
        <!-- tempClass is "normal" (green) or "hot" (red) — set automatically above -->
        <span class="badge {tempClass}">{tempBadge}</span>
      </div>
      <div class="status-row">
        <span class="label">Threshold</span>
        <!-- TODO: change 25.0 here if you change the threshold number above -->
        <span>25.0 &deg;C</span>
      </div>
    </div>

    <!-- LIGHT SENSOR CARD -->
    <div class="card">
      <!-- TODO: update GP27 if your light sensor is on a different pin -->
      <h3>Light Level &middot; GP27</h3>
      <!-- lightValue comes from read_light() -->
      <div class="value">{lightValue} <span class="unit">lux</span></div>
      <div class="status-row" style="margin-top:8px">
        <span class="label">White LED</span>
        <!-- whiteLedClass is "on" (green) or "off" (red) — tracked by white_status variable -->
        <span class="badge {whiteLedClass}">{whiteLedStatus}</span>
      </div>
      <div class="btn-row">
        <!-- these send /?light=on and /?light=off back to the Pico -->
        <a href="/?light=on"  class="btn btn-green">Light ON</a>
        <a href="/?light=off" class="btn btn-red">Light OFF</a>
      </div>
    </div>

    <!-- OCCUPANCY CARD -->
    <div class="card">
      <h3>Occupancy &middot; MMwave</h3>
      <div class="status-row">
        <span class="label">Motion</span>
        <!-- motionClass is "detected" (blue) or "none" (grey) — set from read_mmwave() -->
        <span class="badge {motionClass}">{motionStatus}</span>
      </div>
      <div class="status-row">
        <span class="label">Room state</span>
        <!-- shows "Occupied" or "Empty" based on motionStatus -->
        <span>{"Occupied" if motionStatus == "DETECTED" else "Empty"}</span>
      </div>
    </div>

    <!-- HVAC CARD -->
    <div class="card">
      <h3>HVAC Control</h3>
      <div class="status-row">
        <span class="label">Heating (Red LED)</span>
        <!-- redLedClass is "on" (green) or "off" (red) — tracked by red_status variable -->
        <span class="badge {redLedClass}">{redLedStatus}</span>
      </div>
      <div class="status-row">
        <span class="label">Cooling (Blue LED)</span>
        <!-- blueLedClass is "on" (green) or "off" (red) — tracked by blue_status variable -->
        <span class="badge {blueLedClass}">{blueLedStatus}</span>
      </div>
      <div class="btn-row">
        <!-- these send /?hvac=heat_on etc. back to the Pico -->
        <a href="/?hvac=heat_on"  class="btn btn-red">Heat ON</a>
        <a href="/?hvac=heat_off" class="btn btn-grey">Heat OFF</a>
      </div>
      <div class="btn-row">
        <a href="/?hvac=cool_on"  class="btn btn-blue">Cool ON</a>
        <a href="/?hvac=cool_off" class="btn btn-grey">Cool OFF</a>
      </div>
    </div>

    <!-- SYSTEM MODE CARD -->
    <div class="card full">
      <h3>System Mode</h3>
      <div class="btn-row">
        <!-- these send /?mode=auto etc. back to the Pico -->
        <a href="/?mode=auto"     class="btn btn-blue">Automatic</a>
        <a href="/?mode=manual"   class="btn btn-grey">Manual Override</a>
        <a href="/?mode=vacation" class="btn btn-grey">Vacation Mode</a>
      </div>
      <div class="status-row" style="margin-top:10px">
        <span class="label">Current mode</span>
        <!-- modeStatus is "AUTOMATIC", "MANUAL OVERRIDE", or "VACATION MODE" -->
        <span><b>{modeStatus}</b></span>
      </div>
    </div>

  </div>
</body>
</html>"""
    return str(html)






































































