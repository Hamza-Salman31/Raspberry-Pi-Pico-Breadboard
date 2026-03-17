import machine
import utime

light_sensor = machine.ADC(--)

Vtot = 3.3

print("Reading Lighting: ")

while True:

  raw = light_sensor.read_u16()

  voltage = raw * Vtot / 65535

  resistance = 1000 * voltage / (Vtot - voltage)

  lux = 500 / (resistance ** 1.4)

  print("Resistance:", resistance, "ohms")
  print("Light Level:", lux, "lux")
