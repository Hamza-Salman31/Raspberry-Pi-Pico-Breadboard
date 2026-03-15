
# libraries for wireless communication part
import network
import socket

# Create a function called webpage.
# In this function, create a web page with your desired content.
def webpage():
    html = """<!DOCTYPE html>
<html>
<head>
<style>
h1 {
  color: red;
  position: absolute;
  left: 100px;
  top: 50px;
}
p {
  color: blue;
  position: absolute;
  left: 25px;
  top: 200px;
}
</style>
</head>

<body>
<h1>Welcome</h1>
<p>ENGR 120 Lab</p>
</body>
</html>
"""
    return html


# Create an Access Point
ssid = 'Group3 Pico'       #Set access point name. you can change this. 
password = 'gettingitin'      #Set your access point password. you can use your own password.

# -------------------------------------------------
# Do not change this section of the code
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
#---------------------------------------------------------


# Response when connection received 
while True:
    #-------------------------------------------
    # Do not change the three lines below
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    #---------------------------------------
    
    response = webpage()# respond to the call by loading the function called webpage
    
    # -------------------------------
    # Do not change the following lines of code
    conn.send("HTTP/1.1 200 OK\n")
    conn.send("Content-Type: text/html\n")
    conn.send("Connection: close\n\n")
    conn.sendall(response)
    conn.close()
    # -----------------------------------