import machine
import time
from machine import Pin

# ---------- UART (mmWave sensor) ----------
uart = machine.UART(0, baudrate=256000, tx=machine.Pin(0), rx=machine.Pin(1))

# ---------- LEDs ----------
white_led = Pin(16, Pin.OUT)   # GP16
red_led   = Pin(17, Pin.OUT)   # GP17

# ---------- Frame markers ----------
HDR = b"\xF4\xF3\xF2\xF1"
END = b"\xF8\xF7\xF6\xF5"

STATE = {
    0x00: "no target",
    0x01: "moving",
    0x02: "stationary",
    0x03: "moving+stationary",
}

buf = bytearray()

def le16(b0, b1):
    return b0 | (b1 << 8)

# ---------- TUNING ----------
MAX_CM = 75
MIN_E_MOVE = 35
MIN_E_STAT = 45
OFF_DELAY_S = 8
# --------------------------

last_valid_ms = 0
occupied = False

while True:
    # Read UART
    if uart.any():
        chunk = uart.read()
        if chunk:
            buf.extend(chunk)

    # Process frames
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

        move_cm  = le16(t[1], t[2])
        move_e   = t[3]
        stat_cm  = le16(t[4], t[5])
        stat_e   = t[6]
        detect_cm = le16(t[7], t[8])

        # Distance selection
        if detect_cm != 0:
            dist_cm = detect_cm
        else:
            dist_cm = min(
                move_cm if move_cm > 0 else 9999,
                stat_cm if stat_cm > 0 else 9999
            )

        # Valid target rules
        in_range = (dist_cm > 0) and (dist_cm <= MAX_CM)
        energy_ok = (move_e >= MIN_E_MOVE) or (stat_e >= MIN_E_STAT)
        valid = (status != 0x00) and in_range and energy_ok

        now = time.ticks_ms()

        if valid:
            last_valid_ms = now

        # Occupancy latch with off-delay
        if last_valid_ms == 0:
            occupied = False
        else:
            occupied = time.ticks_diff(
                now, last_valid_ms
            ) <= int(OFF_DELAY_S * 1000)

        # ---------- LED CONTROL ----------
        white_led.value(1 if occupied else 0)
        red_led.value(1 if occupied else 0)
        # --------------------------------

        print(
            "status=", STATE.get(status, hex(status)),
            "| dist=", dist_cm, "cm",
            "| valid=", valid,
            "| OCCUPIED=", occupied
        )

    time.sleep_ms(100)