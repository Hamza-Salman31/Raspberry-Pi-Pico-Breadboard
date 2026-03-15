import machine
import utime

led = machine.Pin(16, machine.Pin.OUT)
infared_sensor = machine.ADC(27)


while True:
    raw = infared_sensor.read_u16()
    
    if raw < 18000:
        print("LED is on")
        led.value(1)
    else:
        print("led is off")
        led.value(0)
    utime.sleep(1)

    
    







