import machine
import time

uart = machine.UART(0, baudrate=256000, tx=machine.Pin(0), rx=machine.Pin(1))

print("Listening...")

while True:
    if uart.any():
        data = uart.read()
        print(data)