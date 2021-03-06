'''
This module defines the behavior of server in your Chat Application
'''
import sys
import getopt
import socket
import util
import threading
import queue

class Server:
    '''
    This is the main Server Class. You will to write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))
        self.window = window

        #store client data (username and address)
        self.clients = {}

        #store client thread info
        self.clientQueues = {}

        #store client acks
        self.clientAckQueues = {}

    def handleClient(self, addr):
        modAddr = ','.join(map(str, addr)) # converts address to string

        loop = True

        while loop:
            packetSeq = []

            check = self.clientQueues.get(modAddr).get()

            #print("From Queue:", check)

            if check[0] == "start":

                packetSeq.append(check)

                while True:
                    # get packets
                    packetSeq.append(self.clientQueues.get(modAddr).get())
                    
                    if packetSeq[-1][0] == "end":
                        break

            #print("Thread of", util.getKeyAtValue(self.clients, addr))

            msg = util.chunkRestorer(packetSeq)
            
            #break message
            msg = util.breakMessage(msg)

            #print(msg)

            if (msg[0] == "join"):
                #check if server full
                if (len(self.clients) == util.MAX_NUM_CLIENTS):
                    # make message
                    snd = util.make_message("ERR_SERVER_FULL", 2)

                    # create a packet sequence for the message
                    list = util.packetSeqCreator(self, snd)

                    # dispatch packet sequence
                    util.dispatchServerPackets(self, list, addr)
                    
                    #disconnect client
                    print("disconnected: server full")
                    loop = False
                    #self.sock.close()
                    
                
                #check if a client with the same username already exists
                elif (str(msg[2]) in self.clients):
                    # make message
                    snd = util.make_message("ERR_USERNAME_UNAVAILABLE", 2)

                    # create a packet sequence for the message
                    list = util.packetSeqCreator(self, snd)

                    # dispatch packet sequence
                    util.dispatchServerPackets(self, list, addr)

                    #disconnect client
                    print("disconnected: username not available")
                    loop = False
                    #self.sock.close()
                    
                    
                #else client joins server successfully
                else:
                    self.clients[msg[2]] = addr
                    print("join:", msg[2])
                    
            elif (msg[0] == "request_users_list"):
                # make message
                respList = util.make_message("response_users_list", 3, ' '.join(self.clients.keys()))

                # create a packet sequence for the message
                list = util.packetSeqCreator(self, respList)

                # dispatch packet sequence
                util.dispatchServerPackets(self, list, addr)
    
                print("request_users_list:", util.getUname(self.clients, addr))
            
            elif (msg[0] == "send_message"):
                #check for invalid inputs
                if (msg[3].isdigit() != True):
                    print("disconnected:", util.getUname(self.clients, addr),"sent unknown command")
                    
                    # make message
                    snd = util.make_message("ERR_UNKNOWN_MESSAGE", 2)
                        
                    # create a packet sequence for the message
                    list = util.packetSeqCreator(self, snd)

                    # dispatch packet sequence
                    util.dispatchServerPackets(self, list, addr)

                    continue
                
                
                print("msg:", util.getUname(self.clients, addr)) #print message
                
                userCount = int(msg[3]) #no of recipients

                recipients = msg[4 : 4 + userCount] #store recipients in list
                
                #remove duplicates
                rec = []
                [rec.append(x) for x in recipients if x not in rec]
                
                paighaam = msg[4 + userCount :] #store msg to be delivered
                paighaam.insert(0, util.getUname(self.clients, addr)) #add sender uname
                paighaam = " ".join(paighaam)
                
                #deliver messages
                for i in recipients:
                    if (i in self.clients):
                        # make message
                        snd = util.make_message("forward_message", 4, paighaam)
                        
                        # create a packet sequence for the message
                        list = util.packetSeqCreator(self, snd)
                        #print(list)
                        # dispatch packet sequence
                        util.dispatchServerPackets(self, list, self.clients[i])
                        
                    else:
                        print("msg:", util.getUname(self.clients, addr), "to non-existent user", i)
            
            elif (msg[0] == "send_file"):
                #check for invalid input
                if (msg[2].isdigit() != True):
                    print("disconnected:", util.getUname(self.clients, addr),"sent unknown command")
                    
                    # make message
                    snd = util.make_message("ERR_UNKNOWN_MESSAGE", 2)
                        
                    # create a packet sequence for the message
                    list = util.packetSeqCreator(self, snd)

                    # dispatch packet sequence
                    util.dispatchServerPackets(self, list, addr)

                    continue
                    
                print("file:", util.getUname(self.clients, addr)) #print message
                
                userCount = int(msg[2]) #no of recipients

                recipients = msg[3 : 3 + userCount] #store recipients in list
                
                #remove duplicates
                rec = []
                [rec.append(x) for x in recipients if x not in rec]
                
                paighaam = msg[3 + userCount :] #store file to be delivered
                paighaam.insert(0, util.getUname(self.clients, addr)) #add sender uname
                paighaam = " ".join(paighaam)
                
                #deliver files
                for i in recipients:
                    if (i in self.clients):
                        # make message
                        snd = util.make_message("forward_file", 4, paighaam)
                        
                        # create a packet sequence for the message
                        list = util.packetSeqCreator(self, snd)

                        # dispatch packet sequence
                        util.dispatchServerPackets(self, list, self.clients[i])

                    else:
                        print("file:", util.getUname(self.clients, addr), "to non-existent user", i)
              
            elif (msg[0] == "disconnect"):
                del self.clients[msg[2]]
                print("disconnected:", msg[2])
                loop = False
                #self.sock.close()

    def start(self):
        '''
        Main loop.
        continue receiving messages from Clients and processing it
        '''

        loop = True

        while loop:
            # listen through socket for client connections
            message, address = self.sock.recvfrom(4096)

            # decode
            pack = message.decode("utf-8")

            # validate checksum and update flag
            flag = util.validate_checksum(pack)

            #drop packet if flag is false
            if flag is False:
                continue

            # parse
            parsedPack = util.parse_packet(pack)

            if parsedPack[0] != "ack":
                # send ack
                self.sock.sendto(util.make_packet("ack", int(parsedPack[1]) + 1).encode("utf-8"), address)

            modAddr = ','.join(map(str, address))  # converts address to string

            # redirect packets to clients based on address
            pack = self.clientQueues.get(modAddr)

            if pack is None and parsedPack[0] == "start":
                # create client threads and assign queues
                self.clientQueues[modAddr] = queue.Queue()
                self.clientAckQueues[modAddr] = queue.Queue()

                clientThread = threading.Thread(target=Server.handleClient, args=(self, address,))
                clientThread.start()

                # redirect packets to clients based on address
                pack = self.clientQueues.get(modAddr)
                pack.put(parsedPack)

            elif parsedPack[0] == "ack":
                self.clientAckQueues.get(modAddr).put(parsedPack)

            else:
                pack.put(parsedPack)

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