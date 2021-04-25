import socket
import threading
import os
import time
import hashlib
import json


class Node:
    def __init__(self, host, port):
        self.stop = False
        self.host = host
        self.port = port
        self.M = 16  # number of bits of hash value
        self.N = 2**self.M  # size of the ring
        self.key = self.hasher(host+str(port))
        # You will need to kill this thread when leaving, to do so just set self.stop = True
        threading.Thread(target=self.listener).start()
        self.files = []
        self.backUpFiles = []
        if not os.path.exists(host+"_"+str(port)):
            os.mkdir(host+"_"+str(port))
        '''
        ------------------------------------------------------------------------------------
        DO NOT EDIT ANYTHING ABOVE THIS LINE
        '''
        # Set value of the following variables appropriately to pass Intialization test
        self.successor = (self.host, self.port)
        self.predecessor = (self.host, self.port)
        self.nextSuccessor = ()

    def hasher(self, key):
        '''
        DO NOT EDIT THIS FUNCTION.
        You can use this function as follows:
                For a node: self.hasher(node.host+str(node.port))
                For a file: self.hasher(file)
        '''
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.N

    def handleConnection(self, client, addr):
        '''
        Function to handle each inbound connection, called as a thread from the listener.
        '''

        # receive message
        msg = client.recv(1024)

        # decode message
        msg = msg.decode("utf-8")

        # check this out (?)
        if msg == "":
            # print(addr)
            return

        msg = json.loads(msg)

        # process message
        if msg[0] == "lookup":
            # make message
            msg.append(self.successor)
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")

            # dispatch message
            client.send(msg)
        
        elif msg[0] == "lookup_req":
            newAddr = (msg[1][0], msg[1][1])
            addr = self.lookUp(newAddr)

            msg.append(addr[0])
            msg.append(addr[1])
        
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")
            client.send(msg)

        elif msg[0] == "peechay_tou_dekho":
            # change predecessor
            msg[0] = "OK"
            msg.append(self.predecessor)
            msg1 = json.dumps(msg)
            msg1 = msg1.encode("utf-8")
            client.send(msg1)

            print(msg)
            self.predecessor = (msg[1][0], msg[1][1])

        elif msg[0] == "aage_tou_dekho":
            # change successor
            msg[0] = "ok"
            msg1 = json.dumps(msg)
            msg1 = msg1.encode("utf-8")
            client.send(msg1)
        
            self.successor = (msg[1][0], msg[1][1])
        
        elif msg[0] == "put":
            self.files.append(msg[1])

            # make message
            msg[0] = "saved"
            msg.append(self.predecessor)
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")

            # dispatch message
            client.send(msg)

            self.recieveFile(client, "localhost_" + str(self.port) + "/" + str(msg[1]))

        elif msg[0] == "put_backup":
            # make message
            msg[0] = "saved"
            msg1 = json.dumps(msg)
            msg1 = msg1.encode("utf-8")

            # dispatch message
            client.send(msg1)
       
            self.backUpFiles.append(msg[1])
        
        elif msg[0] == "get_file":
            # make message
            msg[0] = "sending_file"
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")

            # dispatch message
            client.send(msg)

            self.sendFile(client, "localhost_" + str(self.port) + "/" + str(msg[1]))

        elif msg[0] == "send_backup":
            msg.append(self.backUpFiles)
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")
            
            # dispatch message
            client.send(msg)

        elif msg[0] == "delete_files":
            # make message
            msg[0] = "deleted"
            msg1 = json.dumps(msg)
            msg1 = msg1.encode("utf-8")

            # dispatch message
            client.send(msg1)

            for file in msg[1]:
                if file in self.files:
                    self.files.remove(file)

        elif msg[0] == "leaving_you":
            self.successor = (msg[1][0], msg[1][1])

            msg[0] = "please_don't_leave_me"
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")
            
            # dispatch message
            client.send(msg)

            # ask new successor to change predecessor
            msg1 = ["peechay_tou_dekho", (self.host, self.port)]
            self.sendAndRecv(msg1, self.successor)

            # change next successor
            msg = ["tumhare_aage_kon_hai"]
            msg = self.sendAndRecv(msg, self.successor)

            self.nextSuccessor = (msg[1][0], msg[1][1])

        elif msg[0] == "this_belongs_to_you":
            # store remapped files
            for file in msg[1]:
                self.files.append(file)

            msg = json.dumps(msg)
            msg = msg.encode("utf-8")

            # dispatch message
            client.send(msg)

            # send own files for backup
            msg1 = ["here's_your_stuff", self.files]
            self.sendAndRecv(msg1, self.predecessor)

        elif msg[0] == "don't_leave":
            # store remapped files
            for file in msg[1]:
                self.files.append(file)

            msg = json.dumps(msg)
            msg = msg.encode("utf-8")

            # dispatch message
            client.send(msg)

            # send own files for backup
            msg1 = ["here's_your_stuff", self.files]

            self.sendAndRecv(msg1, self.predecessor)

        elif msg[0] == "here's_your_stuff":
            # update backup
            self.backUpFiles = msg[1]

            msg[0] = "thanks"
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")

            # dispatch message
            client.send(msg)


        elif msg[0] == "ping":
            msg[0] = "still_here_bro"
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")
            
            # dispatch message
            client.send(msg)

        elif msg[0] == "tumhare_aage_kon_hai":
            msg.append(self.successor)
            msg = json.dumps(msg)
            msg = msg.encode("utf-8")
            
            # dispatch message
            client.send(msg)

        elif msg[0] == "file_hai_na_?":
            if str(msg[1]) not in self.files:
                msg[0] = "na"
                msg.append(0)
            else:
                msg[0] = "ha"
                msg.append(1)

            msg = json.dumps(msg)
            msg = msg.encode("utf-8")
            
            # dispatch message
            client.send(msg)

    def listener(self):
        '''
        We have already created a listener for you, any connection made by other nodes will be accepted here.
        For every inbound connection we spin a new thread in the form of handleConnection function. You do not need
        to edit this function. If needed you can edit signature of handleConnection function, but nothing more.
        '''
        listener = socket.socket()
        listener.bind((self.host, self.port))
        listener.listen(10)
        while not self.stop:
            client, addr = listener.accept()
            threading.Thread(target=self.handleConnection,
                             args=(client, addr)).start()
        print("Shutting down node:", self.host, self.port)
        try:
            listener.shutdown(2)
            listener.close()
        except:
            listener.close()

    def lookUp(self, toInsertAddr):
        # get key
        toInsertKey = self.hasher(toInsertAddr[0] + str(toInsertAddr[1]))

        # key and address of current node
        cAddr = (self.host, self.port)
        cKey = self.key
        
        # key and address of current node's successor
        sAddr = self.successor
        sKey = self.hasher(self.successor[0] + str(self.successor[1]))

        # case 1: single node in ring
        if cAddr == sAddr:
            self.predecessor = toInsertAddr
            self.successor = toInsertAddr
            return (cAddr, 1)

        while True:
            if (cKey > sKey) and (toInsertKey > cKey or toInsertKey < sKey):
                return (sAddr, 0)

            elif (cKey < sKey) and (toInsertKey > cKey and toInsertKey < sKey):
                return (sAddr, 0)

            else:
                # create socket
                sock = socket.socket()
                sock.connect((sAddr[0], sAddr[1]))

                # create message
                msg = ["lookup"]

                msg = self.sendAndRecv(msg, sAddr)

                # change current node
                cAddr = sAddr
                cKey = sKey

                # change successor
                sAddr = (msg[1][0], msg[1][1])
                sKey = self.hasher(sAddr[0] + str(sAddr[1]))   
        
    def lookUpFile(self, fileName):
        # get key
        toInsertKey = self.hasher(fileName)

        # key and address of current node
        cAddr = (self.host, self.port)
        cKey = self.key
        
        # key and address of current node's successor
        sAddr = self.successor
        sKey = self.hasher(self.successor[0] + str(self.successor[1]))

        # case 1: single node in ring
        if cAddr == sAddr:
            return (cAddr, 1)

        while True:
            if (cKey > sKey) and (toInsertKey > cKey or toInsertKey < sKey):
                return (sAddr, 0)

            elif (cKey < sKey) and (toInsertKey > cKey and toInsertKey < sKey):
                return (sAddr, 0)

            else:
                # create socket
                sock = socket.socket()
                sock.connect((sAddr[0], sAddr[1]))

                # create message
                msg = ["lookup"]

                msg = self.sendAndRecv(msg, sAddr)

                sock.close()

                # change current node
                cAddr = sAddr
                cKey = sKey

                # change successor
                sAddr = (msg[1][0], msg[1][1])
                sKey = self.hasher(sAddr[0] + str(sAddr[1]))

    def join(self, joiningAddr):
        '''
        This function handles the logic of a node joining. This function should do a lot of things such as:
        Update successor, predecessor, getting files, back up files. SEE MANUAL FOR DETAILS.
        '''

        t1 = threading.Thread(name = 'daemon', target = self.bing)
        t1.setDaemon(True)
        t1.start()

        if joiningAddr != "":
            msg = ["lookup_req", (self.host, self.port)]
            msg = self.sendAndRecv(msg, joiningAddr)

            # key of node already present in DHT
            nodeKey = self.hasher(joiningAddr[0] + str(joiningAddr[1]))

            # successor address
            sAddr = (msg[2][0], msg[2][1])
            flag = msg[3]

            if sAddr == joiningAddr and flag:
                self.predecessor = joiningAddr
                self.successor = joiningAddr
                self.nextSuccessor = (self.host, self.port)

                return

            # update successor
            self.successor = sAddr

            # update next successor
            msg = ["tumhare_aage_kon_hai"]
            msg = self.sendAndRecv(msg, sAddr)

            self.nextSuccessor = (msg[1][0], msg[1][1])
            
            # ask successor to change its predecessor
            msg = ["peechay_tou_dekho", (self.host, self.port)]
            msg = self.sendAndRecv(msg, sAddr)
        
            # change own predecessor
            pAddr = (msg[2][0], msg[2][1])
            self.predecessor = pAddr

            # ask new predecessor to change successor
            msg = ["aage_tou_dekho", (self.host, self.port)]
            self.sendAndRecv(msg, pAddr)

            # print("P" , self.predecessor, self.hasher(self.predecessor[0] + str(self.predecessor[1])))
            # print("C", (self.host, self.port), self.hasher(self.host + str(self.port)))
            # print("S", self.successor, self.hasher(self.successor[0] + str(self.successor[1])))
            # print("NS", self.nextSuccessor, self.hasher(self.nextSuccessor[0] + str(self.nextSuccessor[1])))

            # get file backup from predecessor
            msg = ["send_backup"]
            backup = self.sendAndRecv(msg, self.predecessor)[1]

            # create a list of files that map to curr node
            myKey = self.hasher(self.host + str(self.port))
            mappedFiles = []

            for filename in backup:
                if self.hasher(filename) <= myKey:
                    mappedFiles.append(filename)
                    self.files.append(filename)
                
                else:
                    self.backUpFiles.append(filename)
            
            # ask successor to delete mapped files
            msg = ["delete_files", mappedFiles]
            self.sendAndRecv(msg, self.predecessor)

            # remap backup files


            return
        
    def put(self, fileName):
        '''
        This function should first find node responsible for the file given by fileName, then send the file over the socket to that node
        Responsible node should then replicate the file on appropriate node. SEE MANUAL FOR DETAILS. Responsible node should save the files
        in directory given by host_port e.g. "localhost_20007/file.py".
        '''

        # [('localhost', xxx), 0]
        nodeAddr = self.lookUpFile(fileName)

        # create socket
        sock = socket.socket()
        sock.connect(nodeAddr[0])

        # create and send message
        msg = ["put", fileName]

        # encode message
        msg = json.dumps(msg)
        msg = msg.encode("utf-8")

        # send message
        sock.send(msg)

        # await reply
        msg = sock.recv(1024)

        # decode message
        msg = msg.decode("utf-8")
        msg = json.loads(msg)

        pAddr = msg[2]

        # dispatch file
        self.sendFile(sock, fileName)
        sock.close()

        # dispatch backup file to predecessor
        sock1 = socket.socket()
        sock1.connect((pAddr[0], pAddr[1]))

        msg = ["put_backup", fileName]
        self.sendAndRecv(msg, (pAddr[0], pAddr[1]))

        sock1.close()
        
    def get(self, fileName):
        '''
        This function finds node responsible for file given by fileName, gets the file from responsible node, saves it in current directory
        i.e. "./file.py" and returns the name of file. If the file is not present on the network, return None.
        '''
        
        # [('localhost', xxx), 0]
        nodeAddr = self.lookUpFile(fileName)

        # ask the returned node if it has the file
        msg = ["file_hai_na_?", fileName]
        msg = self.sendAndRecv(msg, (nodeAddr[0][0], nodeAddr[0][1]))

        if msg[2] == 0:
            return None

        # create socket
        sock = socket.socket()
        sock.connect(nodeAddr[0])

        msg = ["get_file", fileName]

        # encode message
        msg = json.dumps(msg)
        msg = msg.encode("utf-8")

        # send message
        sock.send(msg)

        # await reply
        msg = sock.recv(1024)

        # decode message
        msg = msg.decode("utf-8")
        msg = json.loads(msg)

        # recv file
        self.recieveFile(sock, fileName)
        sock.close()

        return fileName

    def leave(self):
        '''
        When called leave, a node should gracefully leave the network i.e. it should update its predecessor that it is leaving
        it should send its share of file to the new responsible node, close all the threads and leave. You can close listener thread
        by setting self.stop flag to True
        '''

        # print("CURR:", (self.host, self.port))
        # print("SUCC:", self.successor)
        # print("PRE:", self.predecessor)

        # intimate predecessor
        msg = ["leaving_you", self.successor]
        self.sendAndRecv(msg, self.predecessor)

        # send files to successor
        msg = ["don't_leave", self.files]
        msg = self.sendAndRecv(msg, self.successor)

        self.stop = True

    def sendFile(self, soc, fileName):
        '''
        Utility function to send a file over a socket
                Arguments:	soc => a socket object
                                        fileName => file's name including its path e.g. NetCen/PA3/file.py
        '''
        fileSize = os.path.getsize(fileName)
        soc.send(str(fileSize).encode('utf-8'))
        soc.recv(1024).decode('utf-8')
        with open(fileName, "rb") as file:
            contentChunk = file.read(1024)
            while contentChunk != "".encode('utf-8'):
                soc.send(contentChunk)
                contentChunk = file.read(1024)

    def recieveFile(self, soc, fileName):
        '''
        Utility function to recieve a file over a socket
                Arguments:	soc => a socket object
                                        fileName => file's name including its path e.g. NetCen/PA3/file.py
        '''
        fileSize = int(soc.recv(1024).decode('utf-8'))
        soc.send("ok".encode('utf-8'))
        contentRecieved = 0
        file = open(fileName, "wb")
        while contentRecieved < fileSize:
            contentChunk = soc.recv(1024)
            contentRecieved += len(contentChunk)
            file.write(contentChunk)
        file.close()

    def kill(self):
        # DO NOT EDIT THIS, used for code testing
        self.stop = True

    def sendAndRecv(self, msg, addr):
        # create socket
        sock = socket.socket()
        sock.connect(addr)

        # encode message
        msg = json.dumps(msg)
        msg = msg.encode("utf-8")

        # send message
        sock.send(msg)

        # await reply
        msg = sock.recv(1024)

        # close socket
        sock.close()

        # decode message
        msg = msg.decode("utf-8")
        msg = json.loads(msg)

        return msg

    def bing(self):
        """
        pinging function
        """

        pingCount = 1
        i = 0

        while self.stop == False:
            # ping successor
            msg = ["ping"]
            flag = False
        
            try:
                # create socket
                sock = socket.socket()
                sock.connect(self.successor)
            except:
                i += 1
                flag = True

            if flag == False:
                # encode message
                msg = json.dumps(msg)
                msg = msg.encode("utf-8")

                # send message
                sock.send(msg)

                # await reply
                sock.settimeout(0.2)
        
                try:
                    msg = sock.recv(1024)
                except:
                    i += 1

                sock.close()

            # successor down
            if i == pingCount:
                # reset i
                i = 0
                # print("DOWN", (self.host, self.port))

                # update successor
                self.successor = self.nextSuccessor

                # ask successor to update predecessor
                msg = ["peechay_tou_dekho", (self.host, self.port)]
                self.sendAndRecv(msg, self.successor)

                # remap files to successor
                msg = ["this_belongs_to_you", self.backUpFiles]
                self.sendAndRecv(msg, self.successor)
            
            time.sleep(0.5)



                

            

