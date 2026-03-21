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