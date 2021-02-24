'''
This module defines the behavior of server in your Chat Application
'''
import sys
import getopt
import socket
import util

class Server:
    '''
    This is the main Server Class. You will to write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #ipv4 and UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))
        self.window = window

        #store client data (username and address)
        self.clients = {}
        
    def start(self):
        '''
        Main loop.
        continue receiving messages from Clients and processing it
        '''
        
        loop = True
        
        while loop:
            #receiving messages from clients
            message, address = self.sock.recvfrom(4096)
            
            #decode packet
            msg = message.decode("utf-8")
            
            #parse packet
            msg = util.parse_packet(msg)
            msg = str(msg[2])
            
            #break message
            msg = util.breakMessage(msg)
            
            if (msg[0] == "join"):
                #check if server full
                if (len(self.clients) == util.MAX_NUM_CLIENTS):
                    #send server full message
                    #make packet
                    pack = util.make_packet(msg = util.make_message("ERR_SERVER_FULL", 2))
                    self.sock.sendto(pack.encode("utf-8"), address)
                    
                    #disconnect client
                    print("disconnected: server full")
                    #loop = False
                    
                
                #check if a client with the same username already exists
                elif (str(msg[2]) in self.clients):
                    #send username unavailable message
                    #make packet
                    pack = util.make_packet(msg = util.make_message("ERR_USERNAME_UNAVAILABLE", 2))
                    
                    #deliver packet
                    self.sock.sendto(pack.encode("utf-8"), address)
                    
                    #disconnect client
                    print("disconnected: username not available")
                    #loop = False
                    
                    
                #else client joins server successfully
                else:
                    self.clients[msg[2]] = address
                    print("join:", msg[2])
                    
            elif (msg[0] == "request_users_list"):
                #make packet
                pack = util.make_packet(msg = util.make_message("response_users_list", 3, ' '.join(self.clients.keys())))
                
                #deliver packet
                self.sock.sendto(pack.encode("utf-8"), address)
    
                print("request_users_list:", util.getUname(self.clients, address))
            
            elif (msg[0] == "send_message"):
                print(msg)
                #check for invalid inputs
                if (msg[3].isdigit() != True):
                    print("disconnected:", util.getUname(self.clients, address),"sent unknown command")
                    
                    #make packet
                    pack = util.make_packet(msg = util.make_message("ERR_UNKNOWN_MESSAGE", 2))
                        
                    #deliver packet
                    self.sock.sendto(pack.encode("utf-8"), address)
                    
                    continue
                
                
                print("msg:", util.getUname(self.clients, address)) #print message
                
                userCount = int(msg[3]) #no of recipients

                recipients = msg[4 : 4 + userCount] #store recipients in list
                
                #remove duplicates by converting to set and back
                recipients = set(recipients)
                recipients = list(recipients)
                
                paighaam = msg[4 + userCount :] #store msg to be delivered
                paighaam.insert(0, util.getUname(self.clients, address)) #add sender uname
                paighaam = " ".join(paighaam)
                
                #deliver messages
                for i in recipients:
                    if (i in self.clients):
                        #make packet
                        pack = util.make_packet(msg = util.make_message("forward_message", 4, paighaam))
                        
                        #deliver packet
                        self.sock.sendto(pack.encode("utf-8"), self.clients[i])
                    else:
                        print("msg:", util.getUname(self.clients, address), "to non-existent user", i)
            
            elif (msg[0] == "send_file"):
                #check for invalid input
                if (msg[2].isdigit() != True):
                    print("disconnected:", util.getUname(self.clients, address),"sent unknown command")
                    
                    #make packet
                    pack = util.make_packet(msg = util.make_message("ERR_UNKNOWN_MESSAGE", 2))
                        
                    #deliver packet
                    self.sock.sendto(pack.encode("utf-8"), address)
                    
                    continue
                    
                print("file:", util.getUname(self.clients, address)) #print message
                
                userCount = int(msg[2]) #no of recipients

                recipients = msg[3 : 3 + userCount] #store recipients in list
                
                #remove duplicates by converting to set and back
                recipients = set(recipients)
                recipients = list(recipients)
                
                paighaam = msg[3 + userCount :] #store file to be delivered
                paighaam.insert(0, util.getUname(self.clients, address)) #add sender uname
                paighaam = " ".join(paighaam)
                
                #deliver files
                for i in recipients:
                    if (i in self.clients):
                        #make packet
                        pack = util.make_packet(msg = util.make_message("forward_file", 4, paighaam))
                        
                        #deliver
                        self.sock.sendto(pack.encode("utf-8"), self.clients[i])
                    else:
                        print("msg:", util.getUname(self.clients, address), "to non-existent user", i)
              
            elif (msg[0] == "disconnect"):
                del self.clients[msg[2]]
                print("disconnected:", msg[2])
                
# Do not change this part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()