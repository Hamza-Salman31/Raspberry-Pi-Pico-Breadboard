# Wireless Communication using Access Point Mode of RPi Pico W

# Libraries
# libraries for wireless communication part
import network
import socket
# libraries for sensor circuit part
import machine 
import utime # time library could be used instead
import math # library to perform mathematical operations

# Configure GP14 as an output pin. An actuator (red LED) is connected to this pin.
led = machine.Pin(14, machine.Pin.OUT)

# Configure ADC(1), which is GP27, as ADC channel and call it as temp_sensor
temp_sensor = machine.ADC(27)
# define a function to get the status of light sensor
def get_tempSensorValue():
    tempSensorValue = temp_sensor.read_u16() # read the ADC output and store it
# The below equation gives temperature in degree Celcius. Adjust the value 10 in the denominator to calibrate the sensor reading. 
    tempValue = round(((((1/(1/298+(1/3960)*math.log((65535/(tempSensorValue)-1)))) - 273)*1)),1)
    return str(tempValue)
    
# create a web page
def web_page(tempValue):
    # Use f-string to allow for passing the status and updating the webpage dynamically
    html = f""" 
          <!DOCTYPE html>
            <html>
            
            <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
                        
            <style>
                html {{ font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}}
                .buttonGreen {{ background-color: #4CAF50; border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }}
                .buttonRed {{ background-color: #D11D53; border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }}
                text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;
            </style>
            </head>
            
            
            <body>
            
            <form><center>
            <center> <button class="buttonGreen" name="Heat" value="on" type="submit">Heat ON</button>
            <br><br>
            <center> <button class="buttonRed" name="Heat" value="off" type="submit">Heat OFF</button>
            </form>
            
            <p>Ambient temperature is {tempValue} degree Celcius</p>
            
            </body>
            </html>
            """
    return str(html) # return html as a string

# Create an Access Point
ssid = 'RPI_PICO_AP'       #Set access point name. you can change this. 
password = '12345678'      #Set your access point password. you can use your own password.

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)            #activating

while ap.active() == False:
  pass
print('Connection is successful')
print(ap.ifconfig()) # get the ip address of the Pico W. This info will be used to connect to the Pico. 


# Create a socket server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

# Response when connection received 
while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    print(request)
# additional code to allow control of actuator from web page    
    request = str(request)
    Heat_on = request.find('Heat=on')
    Heat_off = request.find('Heat=off')     
    print( 'Heat on = ' + str(Heat_on))
    print( 'Heat off = ' + str(Heat_off))
    if Heat_on != -1:
        led.value(1) # the label led should be same as the one used in line 13.
    if Heat_off != -1:
        led.value(0) # the label led should be same as the one used in line 13.
        
    tempValue = get_tempSensorValue() # get the lightStatus by calling the function.
    response = web_page(tempValue) # respond to the call by loading the web page
    conn.send("HTTP/1.1 200 OK\n")
    conn.send("Content-Type: text/html\n")
    conn.send("Connection: close\n\n")
    conn.sendall(response)
    conn.close()


#     request = str(request)
#     print('Content = %s' % request)

