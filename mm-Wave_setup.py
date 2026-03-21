# MM-Wave setup
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