'''
This file contains basic utility functions that you can use.
'''
import binascii
import random
import sys

MAX_NUM_CLIENTS = 10
TIME_OUT = 0.5 # 500ms
NUM_OF_RETRANSMISSIONS = 3
CHUNK_SIZE = 2 # 1400 Bytes

def validate_checksum(message):
    '''
    Validates Checksum of a message and returns true/false
    '''
    try:
        msg, checksum = message.rsplit('|', 1)
        msg += '|'
        return generate_checksum(msg.encode()) == checksum
    except BaseException:
        return False


def generate_checksum(message):
    '''
    Returns Checksum of the given message
    '''
    return str(binascii.crc32(message) & 0xffffffff)


def make_packet(msg_type="data", seqno=0, msg=""):
    '''
    This will add the header to your message.
    The formats is `<message_type> <sequence_number> <body> <checksum>`
    msg_type can be data, ack, end, start
    seqno is a packet sequence number (integer)
    msg is the actual message string
    '''
    body = "%s|%d|%s|" % (msg_type, seqno, msg)
    checksum = generate_checksum(body.encode())
    packet = "%s%s" % (body, checksum)
    return packet


def parse_packet(message):
    '''
    This function will parse the packet in the same way it was made in the above function.
    '''
    pieces = message.split('|')
    msg_type, seqno = pieces[0:2]
    checksum = pieces[-1]
    data = '|'.join(pieces[2:-1])
    return msg_type, seqno, data, checksum


def make_message(msg_type, msg_format, message=None):
    '''
    This function can be used to format your message according
    to any one of the formats described in the documentation.
    msg_type defines type like join, disconnect etc.
    msg_format is either 1,2,3 or 4
    msg is remaining. 
    '''
    if msg_format == 2:
        msg_len = 0
        return "%s %d" % (msg_type, msg_len)
    if msg_format in [1, 3, 4]:
        msg_len = len(message)
        return "%s %d %s" % (msg_type, msg_len, message)
    return ""


def breakMessage(msg):
    '''
    This function splits the message string into
    a tuple (msg_type, msg_len, message) 
    '''
    return msg.split()


def getUname(dict, addr):
    '''
    gets username from client list using address
    '''
    for k, v in dict.items():
        if (v == addr):
            return k
    
    return "DNE"


def msgChunker(msg):
    '''
    converts message into chunks of 
    size CHUNK_SIZE, stores each chunk 
    on each index of a list that is 
    eventually returned
    '''
    msgSize = len(msg)

    chunkNo = round(msgSize / CHUNK_SIZE)

    chunkyMsg = []  #store a chunk at each index

    for i in range(chunkNo):
        chunkyMsg.append(msg[i * CHUNK_SIZE : (i * CHUNK_SIZE) + CHUNK_SIZE])
    
    return chunkyMsg    


def chunkRestorer(chunklist):
    """
    concatenates main message chunks
    in the data section of each packet
    from all packets for a given message
    """

    temp = ""
    for i in range(len(chunklist)):
        temp += chunklist[i][2]

    return temp


def packetSeqCreator(self, madeMsg):
        """
        takes a message, creates and
        and returns a packet sequence
        """

        # divide main message into chunks and make packets
        chunkedMessage = msgChunker(madeMsg)

        # list to store packets in an ordered sequence
        packetSeq = []

        # generate sequence no for session
        seqNo = random.randint(0, sys.maxsize)

        # append start packet
        packetSeq.insert(0, make_packet("start", seqNo, ))

        # append data packets
        for i in range(len(chunkedMessage)):
            # make and store packets
            packetSeq.append(make_packet("data", seqNo + (2 * i + 2), str(chunkedMessage[i])))

        # append end packet to list
        packetSeq.append(make_packet("end", 2 * (len(chunkedMessage) + 1) + seqNo, ))

        return packetSeq


def dispatchClientPackets(self, packetSeq, addr):
    """
    takes a packet sequence in arg
    created by packetSeqCreator function
    and dispatches these packets systematically
    to the SERVER
    """

    for i in range(len(packetSeq)):
        self.sock.sendto(packetSeq[i].encode("utf-8"), addr)

        ack = self.ackQ.get(block=True)

        if (ack[0] == "ack"):
            # print("ack recvd", ack[1])
            continue


def dispatchServerPackets(self, packetSeq, addr):
    """
    takes a packet sequence in arg
    created by packetSeqCreator function
    and dispatches these packets systematically
    to the CLIENT
    """
    modAddr = ','.join(map(str, addr))  # converts address to string

    for i in range(len(packetSeq)):
        self.sock.sendto(packetSeq[i].encode("utf-8"), addr)

        ack = self.clientQueues.get(modAddr).get(block=True)

        if (ack[0] == "ack"):
            # print("ack recvd", ack[1])
            continue