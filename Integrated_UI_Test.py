import network
import socket
import machine
import time
import math
from machine import Pin

# ======================================================
# WIFI ACCESS POINT
# ======================================================
ssid = 'GROUP_3'
password = 'onetwothreefourfive67'

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)

while not ap.active():
    time.sleep_ms(100)

ip_address = ap.ifconfig()[0]
print('Access point active!')
print('IP address:', ip_address)

# ======================================================
# SENSOR / HARDWARE SETUP
# ======================================================
Vtot = 3.3

# Temp sensor on GP26
temp_sensor = machine.ADC(26)
TEMP_R_FIXED = 10000
TEMP_R0 = 100000
TEMP_T0 = 298.15
TEMP_B = 4014

# Light sensor on GP27
light_sensor = machine.ADC(27)
LIGHT_R_FIXED = 10000
R_REF = 7300.0
LUX_REF = 300.0
GAMMA = 1.7

# MM-wave on UART0
uart = machine.UART(0, baudrate=256000, tx=machine.Pin(0), rx=machine.Pin(1))
HDR = b"\xF4\xF3\xF2\xF1"
END = b"\xF8\xF7\xF6\xF5"
buf = bytearray()

MAX_CM = 100
MIN_E_MOVE = 30
MIN_E_STAT = 30
OFF_DELAY_S = 8
FAIL_TIMEOUT_S = 5

last_valid_ms = 0
last_uart_ms = time.ticks_ms()

# LEDs
white_led = Pin(16, Pin.OUT)   # lighting
red_led = Pin(17, Pin.OUT)     # heating
blue_led = Pin(18, Pin.OUT)    # cooling

# ======================================================
# CONTROL SETTINGS
# ======================================================
LIGHT_THRESHOLD = 100
TEMP_TOO_HOT = 30
TEMP_TOO_COLD = 26
LOG_INTERVAL_MS = 1000

system_mode = 'AUTOMATIC'
manual_white = False
manual_red = False
manual_blue = False

latest_state = {
    'tempC': None,
    'lux': None,
    'motionStatus': 'NONE',
    'motionClass': 'none',
    'whiteStatus': 'OFF',
    'whiteClass': 'off',
    'redStatus': 'OFF',
    'redClass': 'off',
    'blueStatus': 'OFF',
    'blueClass': 'off',
    'modeStatus': system_mode,
    'conditions': ['System starting...']
}

# ======================================================
# SENSOR FUNCTIONS
# ======================================================
def read_temperature():
    total = 0
    for _ in range(20):
        total += temp_sensor.read_u16()
        time.sleep_ms(10)

    raw = total / 20
    voltage = raw * Vtot / 65535

    if voltage <= 0 or voltage >= Vtot:
        return None

    resistance = TEMP_R_FIXED * voltage / (Vtot - voltage)
    tempK = 1 / ((1 / TEMP_T0) + (1 / TEMP_B) * math.log(resistance / TEMP_R0))
    return tempK - 273.15


def read_light():
    total = 0
    for _ in range(20):
        total += light_sensor.read_u16()
        time.sleep_ms(5)

    raw = total / 20
    voltage = raw * Vtot / 65535

    if voltage >= Vtot:
        return None

    resistance = LIGHT_R_FIXED * voltage / (Vtot - voltage)
    lux = LUX_REF * (R_REF / resistance) ** GAMMA
    return lux


def le16(b0, b1):
    return b0 | (b1 << 8)


def read_mmwave():
    global buf, last_valid_ms, last_uart_ms

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

        frame = bytes(buf[start:end + 4])
        buf = buf[end + 4:]

        if len(frame) < 23:
            continue

        data_type = frame[6]
        head = frame[7]

        if data_type != 0x02 or head != 0xAA:
            continue

        t = frame[8:17]
        status = t[0]

        move_cm = le16(t[1], t[2])
        move_e = t[3]
        stat_cm = le16(t[4], t[5])
        stat_e = t[6]
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

        if valid:
            last_valid_ms = time.ticks_ms()

    now = time.ticks_ms()

    if last_valid_ms == 0:
        occupied = False
    else:
        occupied = time.ticks_diff(now, last_valid_ms) <= int(OFF_DELAY_S * 1000)

    if time.ticks_diff(time.ticks_ms(), last_uart_ms) > int(FAIL_TIMEOUT_S * 1000):
        occupied = False

    return occupied

# ======================================================
# WEB PAGE
# ======================================================
def web_page(state):
    tempC = state['tempC']
    lightValue = state['lux']
    motionStatus = state['motionStatus']
    motionClass = state['motionClass']
    whiteLedStatus = state['whiteStatus']
    whiteLedClass = state['whiteClass']
    redLedStatus = state['redStatus']
    redLedClass = state['redClass']
    blueLedStatus = state['blueStatus']
    blueLedClass = state['blueClass']
    modeStatus = state['modeStatus']
    conditions = state['conditions']

    if blueLedStatus == 'ON':
        alertStyle = 'display:block'
        alertText = 'High temperature detected! HVAC cooling activated.'
    elif redLedStatus == 'ON':
        alertStyle = 'display:block'
        alertText = 'Low temperature detected! HVAC heating activated.'
    else:
        alertStyle = 'display:none'
        alertText = ''

    if tempC is None:
        tempDisplay = 'ERR'
        tempBadge = 'ERROR'
        tempClass = 'off'
    elif tempC >= TEMP_TOO_HOT:
        tempDisplay = str(round(tempC, 2))
        tempBadge = 'HOT'
        tempClass = 'hot'
    elif tempC <= TEMP_TOO_COLD:
        tempDisplay = str(round(tempC, 2))
        tempBadge = 'COLD'
        tempClass = 'detected'
    else:
        tempDisplay = str(round(tempC, 2))
        tempBadge = 'NORMAL'
        tempClass = 'normal'

    if lightValue is None:
        lightDisplay = 'ERR'
    else:
        lightDisplay = str(round(lightValue, 1))

    condition_html = ''.join(
        '<div class="status-row"><span class="label">&bull;</span><span>{}</span></div>'.format(item)
        for item in conditions
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Smart Room Control</title>
  <meta http-equiv="refresh" content="5">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 760px; margin: 0 auto; padding: 20px; background: #003B5C; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 4px; color: white; }}
    p.sub {{ color: #cce5ff; font-size: 0.85rem; margin-top: 0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }}
    .card {{ background: white; border-radius: 8px; padding: 14px 16px; border: 1px solid #ddd; }}
    .card h3 {{ font-size: 0.75rem; text-transform: uppercase; color: #999; margin: 0 0 10px 0; letter-spacing: 0.08em; }}
    .value {{ font-size: 1.8rem; font-weight: bold; color: #222; }}
    .unit {{ font-size: 0.9rem; color: #888; }}
    .status-row {{ display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; gap: 8px; }}
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
  <h1>Smart Room Energy Management</h1>
  <p class="sub">Group 3 &mdash; B02 &nbsp;|&nbsp; Raspberry Pi Pico W &nbsp;|&nbsp; Auto-refresh: 5s &nbsp;|&nbsp; {ip_address}</p>

  <div class="alert" style="{alertStyle}">{alertText}</div>

  <div class="grid">
    <div class="card">
      <h3>Temperature &middot; GP26</h3>
      <div class="value">{tempDisplay} <span class="unit">&deg;C</span></div>
      <div class="status-row" style="margin-top:8px">
        <span class="label">Status</span>
        <span class="badge {tempClass}">{tempBadge}</span>
      </div>
      <div class="status-row">
        <span class="label">Hot threshold</span>
        <span>{TEMP_TOO_HOT:.1f} &deg;C</span>
      </div>
      <div class="status-row">
        <span class="label">Cold threshold</span>
        <span>{TEMP_TOO_COLD:.1f} &deg;C</span>
      </div>
    </div>

    <div class="card">
      <h3>Light Level &middot; GP27</h3>
      <div class="value">{lightDisplay} <span class="unit">lux</span></div>
      <div class="status-row" style="margin-top:8px">
        <span class="label">White LED</span>
        <span class="badge {whiteLedClass}">{whiteLedStatus}</span>
      </div>
      <div class="status-row">
        <span class="label">Dim threshold</span>
        <span>{LIGHT_THRESHOLD}</span>
      </div>
      <div class="btn-row">
        <a href="/?light=on" class="btn btn-green">Light ON</a>
        <a href="/?light=off" class="btn btn-red">Light OFF</a>
      </div>
    </div>

    <div class="card">
      <h3>Occupancy &middot; MMwave</h3>
      <div class="status-row">
        <span class="label">Motion</span>
        <span class="badge {motionClass}">{motionStatus}</span>
      </div>
      <div class="status-row">
        <span class="label">Room state</span>
        <span>{'Occupied' if motionStatus == 'DETECTED' else 'Empty'}</span>
      </div>
    </div>

    <div class="card">
      <h3>HVAC Control</h3>
      <div class="status-row">
        <span class="label">Heating (Red LED)</span>
        <span class="badge {redLedClass}">{redLedStatus}</span>
      </div>
      <div class="status-row">
        <span class="label">Cooling (Blue LED)</span>
        <span class="badge {blueLedClass}">{blueLedStatus}</span>
      </div>
      <div class="btn-row">
        <a href="/?hvac=heat_on" class="btn btn-red">Heat ON</a>
        <a href="/?hvac=heat_off" class="btn btn-grey">Heat OFF</a>
      </div>
      <div class="btn-row">
        <a href="/?hvac=cool_on" class="btn btn-blue">Cool ON</a>
        <a href="/?hvac=cool_off" class="btn btn-grey">Cool OFF</a>
      </div>
    </div>

    <div class="card full">
      <h3>System Mode</h3>
      <div class="btn-row">
        <a href="/?mode=auto" class="btn btn-blue">Automatic</a>
        <a href="/?mode=manual" class="btn btn-grey">Manual Override</a>
        <a href="/?mode=vacation" class="btn btn-grey">Vacation Mode</a>
      </div>
      <div class="status-row" style="margin-top:10px">
        <span class="label">Current mode</span>
        <span><b>{modeStatus}</b></span>
      </div>
    </div>

    <div class="card full">
      <h3>Live Conditions</h3>
      {condition_html}
    </div>
  </div>
</body>
</html>"""
    return html

# ======================================================
# REQUEST HANDLING
# ======================================================
def handle_actions(request_text):
    global system_mode, manual_white, manual_red, manual_blue

    if '/?mode=auto' in request_text:
        system_mode = 'AUTOMATIC'
    elif '/?mode=manual' in request_text:
        system_mode = 'MANUAL OVERRIDE'
    elif '/?mode=vacation' in request_text:
        system_mode = 'VACATION MODE'

    if '/?light=on' in request_text:
        manual_white = True
    elif '/?light=off' in request_text:
        manual_white = False

    if '/?hvac=heat_on' in request_text:
        manual_red = True
        manual_blue = False
    elif '/?hvac=heat_off' in request_text:
        manual_red = False

    if '/?hvac=cool_on' in request_text:
        manual_blue = True
        manual_red = False
    elif '/?hvac=cool_off' in request_text:
        manual_blue = False


def set_outputs(white_on, red_on, blue_on):
    white_led.value(1 if white_on else 0)
    red_led.value(1 if red_on else 0)
    blue_led.value(1 if blue_on else 0)


def update_system_state():
    occupied = read_mmwave()
    lux = read_light()
    tempC = read_temperature()

    white_on = False
    red_on = False
    blue_on = False
    conditions = []

    if system_mode == 'AUTOMATIC':
        if occupied and lux is not None and lux <= LIGHT_THRESHOLD:
            white_on = True

        if occupied and tempC is not None:
            if tempC > TEMP_TOO_HOT:
                blue_on = True
            elif tempC < TEMP_TOO_COLD:
                red_on = True

    elif system_mode == 'MANUAL OVERRIDE':
        white_on = manual_white
        red_on = manual_red
        blue_on = manual_blue

    elif system_mode == 'VACATION MODE':
        white_on = False
        red_on = False
        blue_on = False

    set_outputs(white_on, red_on, blue_on)

    conditions.append('Occupied' if occupied else 'Unoccupied')

    if lux is None:
        conditions.append('Light sensor error')
    elif lux <= LIGHT_THRESHOLD:
        conditions.append('Room is dim')
    else:
        conditions.append('Room is bright enough')

    if tempC is None:
        conditions.append('Temp sensor error')
    elif tempC > TEMP_TOO_HOT:
        conditions.append('Room is too hot')
    elif tempC < TEMP_TOO_COLD:
        conditions.append('Room is too cold')
    else:
        conditions.append('Room temperature is okay')

    if system_mode == 'MANUAL OVERRIDE':
        conditions.append('Manual commands control the LEDs')
    elif system_mode == 'VACATION MODE':
        conditions.append('Vacation mode keeps all actuators off')
    else:
        conditions.append('Automatic control active')

    return {
        'tempC': tempC,
        'lux': lux,
        'motionStatus': 'DETECTED' if occupied else 'NONE',
        'motionClass': 'detected' if occupied else 'none',
        'whiteStatus': 'ON' if white_led.value() else 'OFF',
        'whiteClass': 'on' if white_led.value() else 'off',
        'redStatus': 'ON' if red_led.value() else 'OFF',
        'redClass': 'on' if red_led.value() else 'off',
        'blueStatus': 'ON' if blue_led.value() else 'OFF',
        'blueClass': 'on' if blue_led.value() else 'off',
        'modeStatus': system_mode,
        'conditions': conditions
    }


def print_state(state):
    print('================================')

    if state['tempC'] is None:
        print('Temperature: ERROR')
    else:
        print('Temperature:', round(state['tempC'], 2), 'C')

    if state['lux'] is None:
        print('Light Level: ERROR')
    else:
        print('Light Level:', round(state['lux'], 1), 'lux')

    print('Motion:', state['motionStatus'])
    print('White LED (Lighting):', state['whiteStatus'])
    print('Blue LED (Cooling):', state['blueStatus'])
    print('Red LED (Heating):', state['redStatus'])
    print('Mode:', state['modeStatus'])
    print('Conditions:')
    for item in state['conditions']:
        print('-', item)
    print()

# ======================================================
# SOCKET SERVER
# ======================================================
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)
s.settimeout(0.2)

print('Web server ready at http://{}/'.format(ip_address))
print('Starting room test...')

last_log_ms = time.ticks_ms() - LOG_INTERVAL_MS

try:
    while True:
        now = time.ticks_ms()

        if time.ticks_diff(now, last_log_ms) >= LOG_INTERVAL_MS:
            latest_state = update_system_state()
            print_state(latest_state)
            last_log_ms = now

        try:
            conn, addr = s.accept()
            request = conn.recv(1024)
            request_text = request.decode('utf-8') if request else ''

            handle_actions(request_text)

            # Refresh state immediately after a button press
            latest_state = update_system_state()

            response = web_page(latest_state)
            conn.send('HTTP/1.1 200 OK\r\n')
            conn.send('Content-Type: text/html\r\n')
            conn.send('Connection: close\r\n\r\n')
            conn.sendall(response)
            conn.close()

        except OSError:
            pass

        time.sleep_ms(50)

except KeyboardInterrupt:
    set_outputs(False, False, False)
    s.close()
    print('System stopped.')
