import machine
import time

uart = machine.UART(0, baudrate=256000, tx=machine.Pin(0), rx=machine.Pin(1))
from machine import Pin

led = Pin(16, Pin.OUT)   # GP15
red_led = Pin(17, Pin.OUT)


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

# --- TUNING ---
MAX_CM = 75         # ignore anything farther than this (through-wall usually shows up farther)
MIN_E_MOVE = 35       # minimum moving energy to count
MIN_E_STAT = 45       # minimum stationary energy to count
OFF_DELAY_S = 8       # if no valid target for this long => occupied False
# ---------------------------

last_valid_ms = 0
occupied = False

while True:
    if uart.any():
        data = uart.read()
        if data:
            buf.extend(data)

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

        # Decide which distance to trust for gating
        # Use detect_cm if present, otherwise fall back to the closer of move/stat
        if detect_cm != 0:
            dist_cm = detect_cm
        else:
            # some firmwares output 0 here often
            dist_cm = min(move_cm if move_cm > 0 else 9999,
                          stat_cm if stat_cm > 0 else 9999)

        # Valid target rules (range gate + energy gate)
        in_range = (dist_cm > 0) and (dist_cm <= MAX_CM)
        energy_ok = (move_e >= MIN_E_MOVE) or (stat_e >= MIN_E_STAT)

        valid = (status != 0x00) and in_range and energy_ok

        now = time.ticks_ms()
        if valid:
            last_valid_ms = now

        # latch occupancy with an off-delay
        if last_valid_ms == 0:
            occupied = False
        else:
            occupied = time.ticks_diff(now, last_valid_ms) <= int(OFF_DELAY_S * 1000)
            led.value(occupied)

        print(
            "status=", STATE.get(status, hex(status)),
            "| move=", move_cm, "cm (E", move_e, ")",
            "| stat=", stat_cm, "cm (E", stat_e, ")",
            "| detect=", detect_cm, "cm",
            "| dist_used=", dist_cm, "cm",
            "| valid=", valid,
            "| OCCUPIED=", occupied
        )

    time.sleep_ms(100)