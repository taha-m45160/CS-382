'''
Part 2.1
This module defines the behavior of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import util
import queue
import time

'''
Write your code inside this class. 
In the start() function, you will read user-input and act accordingly.
receive_handler() function is running another thread and you have to listen 
for incoming messages in this function.
'''

class Client:
    '''
    This is the main Client Class. 
    '''

    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.window = window_size

        self.ackQ = queue.Queue()

    def start(self):
        """
        Main Loop is here
        Start by sending the server a JOIN message.
        Waits for userinput and then processes it
        """
        # make join message
        joinMsg = util.make_message("join", 1, self.name)

        # create a packet sequence for the message
        join = util.packetSeqCreator(self, joinMsg)

        # dispatch packet sequence
        util.dispatchClientPackets(self, join, (self.server_addr, self.server_port))

        loop = True

        while loop:
            msg = input()

            if (msg == "list"):
                # make list message
                listMsg = util.make_message("request_users_list", 2)

                # create a packet sequence for the message
                list = util.packetSeqCreator(self, listMsg)

                # dispatch packet sequence
                util.dispatchClientPackets(self, list, (self.server_addr, self.server_port))

            elif (msg[:3] == "msg"):
                # make list message
                listMsg = util.make_message("send_message", 4, msg)

                # create a packet sequence for the message
                list = util.packetSeqCreator(self, listMsg)

                # dispatch packet sequence
                util.dispatchClientPackets(self, list, (self.server_addr, self.server_port))

            elif (msg[:4] == "file"):
                # get file info
                userInput = util.breakMessage(msg)
                fileName = userInput[-1]

                # handle file
                file = open(fileName, 'r')
                msg = file.read()  # contains file
                finalMsg = ' '.join(userInput[1:]) + " " + msg

                # send file to server
                # make message
                listMsg = util.make_message("send_file", 4, finalMsg)

                # create a packet sequence for the message
                list = util.packetSeqCreator(self, listMsg)

                # dispatch packet sequence
                util.dispatchClientPackets(self, list, (self.server_addr, self.server_port))

            elif (msg == "quit"):
                print("quitting")
                loop = False

                # make quit message
                quitMsg = util.make_message("disconnect", 1, self.name)

                # create a packet sequence for the message
                quit = util.packetSeqCreator(self, quitMsg)

                # dispatch packet sequence
                util.dispatchClientPackets(self, quit, (self.server_addr, self.server_port))

                #self.sock.close()

            elif (msg == "help"):
                print("Help:")
                print("Message: msg <number_of_users> <username1> <username2> … <message>")
                print("Available Users: list")
                print("File Sharing: file <number_of_users> <username1> <username2> … <file_name>")
                print("Quit: quit")

            else:
                print("incorrect userinput")

    def receive_handler(self):
        '''
        Waits for a message from server and process it accordingly
        '''

        loop = True
        packetSeq = []

        while loop:

            # listen through socket for server messages
            message, address = self.sock.recvfrom(4096)
            #print("Thread of", self.name)

            # decode and parse
            pack = message.decode("utf-8")
            parPack = util.parse_packet(pack)

            #print(parPack)

            # check for ack
            if parPack[0] == "ack":
                self.ackQ.put(parPack)
                continue

            else:
                packetSeq.append(parPack)

                self.sock.sendto(util.make_packet("ack", int(parPack[1]) + 1).encode("utf-8"), address)

                if packetSeq[-1][0] != "end":
                    continue

            #print(packetSeq)

            msg = util.chunkRestorer(packetSeq)

            # break message
            msg = util.breakMessage(msg)

            if (msg[0] == "ERR_SERVER_FULL"):
                # disconnect from server
                print("disconnected: server full")
                loop = False
                #self.sock.close()
                #break

            elif (msg[0] == "ERR_USERNAME_UNAVAILABLE"):
                # disconnect from server
                print("disconnected: username not available")
                loop = False
                #self.sock.close()
                #break

            elif (msg[0] == "ERR_UNKNOWN_MESSAGE"):
                # disconnect from server
                print("disconnected: server received an unknown command")
                loop = False
                #self.sock.close()
                #break

            elif (msg[0] == "response_users_list"):
                print("list:", ' '.join(sorted(msg[2:])))

            elif (msg[0] == "forward_message"):
                print("msg:", ''.join(msg[2] + ":"), ' '.join(msg[3:]))

            elif (msg[0] == "forward_file"):
                fileName = self.name + "_" + str(msg[3])  # client_name + file_name
                file = open(fileName, "w")

                # display file received message
                print("file:", ''.join(str(msg[2] + ":")), str(msg[3]))

                # write to new file
                file.write(' '.join(msg[4:]))
                file.close()

            packetSeq = []

# Do not change this part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")


    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=", "window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
