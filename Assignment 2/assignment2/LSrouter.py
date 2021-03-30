import sys
from collections import defaultdict
from router import Router
from packet import Packet
import json
from dijkstar import Graph, find_path


class LSrouter(Router):
    """Link state routing protocol implementation."""

    def __init__(self, addr, heartbeatTime):
        """TODO: add your own class fields and initialization code here"""
        Router.__init__(self, addr)  # initialize superclass - don't remove
        self.heartbeatTime = heartbeatTime
        self.last_time = 0
        self.seqNo = 0
        self.localState = {}
        self.linkStates = {}
        self.fwdTable = {}
        self.myNetwork = Graph(undirected = True)
        self.trackSeq = {}



    def handlePacket(self, port, packet):
        """TODO: process incoming packet"""
        if packet.isTraceroute():
            #   send packet based on forwarding table
            if packet.dstAddr in self.fwdTable:
                self.send(self.fwdTable[packet.dstAddr], packet)

            else:
                #print(packet.srcAddr, "to", packet.dstAddr, "via", self.addr, self.fwdTable)
                pass
    
        else:
            # process state and seqNo from incoming packet
            state = json.loads(packet.content)
            seqNo = state["seqNo"]
            del state["seqNo"]

            # source address of routing packet
            endpoint = packet.srcAddr
            print(endpoint)

            currSeqNo = self.trackSeq.get(endpoint)
            print("CURR:", currSeqNo)

            print("Updated:", seqNo)

            # check for seqNo
            if currSeqNo is None:
                pass

            elif currSeqNo >= seqNo:
                return

            self.trackSeq[endpoint] = seqNo

            # update the local copy of the link state
            if self.linkStates.get(endpoint) is None:
                self.linkStates[endpoint] = state

            elif self.linkStates.get(endpoint) is not state:
                # reset network graph for endpoint
                for n in self.linkStates[endpoint].keys():
                    self.myNetwork.remove_edge(endpoint, n)

                self.linkStates[endpoint] = state

            else:
                return

            # update network graph
            for n, c in state.items():
                self.myNetwork.add_edge(endpoint, n, c)

            # update the forwarding table
            self.runDijkstar()

            # broadcast the packet to other neighbors
            self.broadcastState()

        return


    def handleNewLink(self, port, endpoint, cost):
        """TODO: handle new link"""

        # update link state version
        self.seqNo += 1
        self.trackSeq[self.addr] = self.seqNo

        # update link state
        self.localState[endpoint] = cost
        self.linkStates[self.addr] = self.localState

        # update network graph
        self.myNetwork.add_edge(self.addr, endpoint, cost)

        # update the forwarding table
        self.updateFwdTable(endpoint, port)

        # broadcast the new link state of this router to all neighbors
        self.broadcastState()


    def handleRemoveLink(self, port):
        """TODO: handle removed link"""
        
        # update link state version
        self.seqNo += 1
        self.trackSeq[self.addr] = self.seqNo

        # update link state
        endpoint = self.getKey(self.fwdTable, port)
        del self.localState[endpoint]
        self.linkStates[self.addr] = self.localState

        # update network graph
        self.myNetwork.remove_edge(self.addr, endpoint)

        # update the forwarding table
        self.updateFwdTable(endpoint, port, True)

        # broadcast the new link state of this router to all neighbors
        self.broadcastState()


    def handleTime(self, timeMillisecs):
        """TODO: handle current time"""
        if timeMillisecs - self.last_time >= self.heartbeatTime:
            self.last_time = timeMillisecs
            # Hints:
            # broadcast the link state of this router to all neighbors
            self.broadcastState()


    def debugString(self):
        """TODO: generate a string for debugging in network visualizer"""
        return ""


    def getKey(self, dict, val):
        """
        returns the key in a
        dictionary given the value
        against that key
        """

        for k, v in dict.items():
            if v == val:
                return k
        
        else:
            return None


    def updateFwdTable(self, endpoint, port, remove = False):
        """
        updates the forwarding table by including 
        a newly added link or removing a 
        recently deleted link and then runs dijkstar
        to update the paths of rest of the nodes
        in the network
        """

        if not remove:
            # add new link entry
            self.fwdTable[endpoint] = port
        
        else:
            # remove link entry
            del self.fwdTable[endpoint]

        # update nodes in fwd table
        for k in self.myNetwork.keys():
            # assuming that neighbors already present
            if k not in self.localState.keys():
                self.fwdTable[k] = k

        for k in self.fwdTable.keys():
            if k not in self.myNetwork.keys():
                del self.fwdTable[k]

        self.runDijkstar()

        return

    
    def broadcastState(self):
        state = self.localState
        state["seqNo"] = self.seqNo
        state = json.dumps(state)
        
        for node, port in self.fwdTable.items():
            if node is not self.addr:
                self.send(port, Packet(2, self.addr, node, state))

        return


    def runDijkstar(self):
        """
        updates paths of the nodes that
        are not the immediate neighbors 
        of the concerned router
        """

        # reset forwarding table
        for node in list(self.fwdTable.keys()):
            if node not in self.localState.keys():
                del self.fwdTable[node]
        

        # add nodes from graph
        for node in self.myNetwork.keys():
            if node == self.addr:
                continue

            if node not in self.localState.keys():
                try:
                    pathInfo = find_path(self.myNetwork, self.addr, node)
                except:
                    continue

                self.fwdTable[node] = self.fwdTable[pathInfo.nodes[1]]

                        
        return
