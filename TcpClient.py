# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng
import os
from TcpConnector import *
from protocol_filetransfer import *



class TcpClient(TcpConnector):
    def __init__(self,connType,ip,port,messageQueue):
        super(TcpClient,self).__init__(connType,ip,port,messageQueue)
        pass

    #How unpack a packet from buffer
    def unpackFromBuffer(self,leftBuffer):
        leftSize=len(leftBuffer)
        if leftSize <FILE_TRANSFER_HEAD.getSize():
            return 0
        net_head_data=leftBuffer[0:FILE_TRANSFER_HEAD.getSize()]
        net_head = FILE_TRANSFER_HEAD()
        net_head.unpack(net_head_data)
        if net_head.muSize > COMMON.MAX_PACKET_SIZE  or   net_head.muSize < COMMON.MIN_PACKET_SIZE:
            print "[TcpClient] unpackFromBuffer packetSize:{0} error:".format(net_head.muSize)
            return -1
        if leftSize < net_head.muSize:
            return 0
        return net_head.muSize
        pass
    
    def sendPacket(self,packet):
        data=packet.pack()
        self.sendData(data)
        #print "sendPacket->cmd:{0} size:{1}".format(packet.muCmd,packet.muSize)











            
        
