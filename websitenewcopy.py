import network
import socket

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