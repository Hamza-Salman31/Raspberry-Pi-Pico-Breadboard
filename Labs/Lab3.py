import machine
import utime
sensor1 = machine.ADC(26)
Vtot = 3.3
print("Reading sensor:")
while True:
    raw = sensor1.read_u16()
    voltage2 = raw * Vtot / 65535
    resistance = voltage2 * 1 / (Vtot - voltage2)
    print("temp resistor value", resistance)
    utime.sleep(2)

