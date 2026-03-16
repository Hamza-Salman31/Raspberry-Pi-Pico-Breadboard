import machine
import utime
import math

temp_sensor = machine.ADC(26)

Vtot = 3.3

R_FIXED = 1000    
R0 = 1000           
T0 = 298.15       
B = 3950             

print("Reading temperature:")

while True:

    raw = temp_sensor.read_u16()

    voltage = raw * Vtot / 65535

    resistance = R_FIXED * voltage / (Vtot - voltage)

    tempK = 1 / ((1/T0) + (1/B) * math.log(resistance / R0))

    tempC = tempK - 273.15

    print("Resistance:", resistance, "ohms")
    print("Temperature:", tempC, "°C")
    print()

    utime.sleep(2)
