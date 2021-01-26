import socket

s = socket.socket() #no arguments so ipv4 and TCP by default
print("Socket created")

s.bind(('localhost', 9999))

s.listen(3) 

print("Waiting for connections")

while True:
    c, addr = s.accept()
    print("Connected with ", addr)

    c.send("Welcome to Lahore")

    c.close()