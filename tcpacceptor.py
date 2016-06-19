# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng
import sys,os
import Queue,time
import socket,select,errno
from config import *
from common import *

def getNowTime():
    t=time.time()
    return int(t)

class SocketStatus:
    SOCKET_INIT=0
    SOCKET_CONNECTING=1
    SOCKET_CONNECTED=2
    SOCKET_WOULDCLOSE=3
    SOCKET_CLOSED=4
    
###################################################
# TcpAcceptor 接受器，用户包装accept后的连接
# 子类继承TcpAcceptor，可Overrid以下方法：
# unpackFromBuffer 定制解包逻辑
# makeTask   定制把接收数据包装成一个任务的方法，此task存放在接收队列里
###################################################
class TcpAcceptor(object):    
    def __init__(self,serverType,acceptSocket,acceptAddr,msgQueue=None):                     
        self.serverType=serverType
        self.acceptSocket=acceptSocket
        self.acceptAddr=acceptAddr
        if msgQueue:
            self.messageQueue=msgQueue
        else:            
            self.messageQueue=Queue.Queue()
        self.socketState=SocketStatus.SOCKET_CONNECTED    
        self.recvBuffer=""
        self.recvBufSize=1024
        self.keepliveTime=getNowTime()
        self.sessionId=0        
    def dumpLog(self,info):
        logText="[ses{0}{1}] {2}".format(self.sessionId,self.acceptAddr,info)
        dump_log(logText)

    def setSessionId(self,sessionId):
        self.sessionId = sessionId          
    def getSessionId(self):
        return self.sessionId    
    def disconnect(self,is_release=True):
        if not is_release:
            self.socketState=SocketStatus.SOCKET_WOULDCLOSE
            return
        if SocketStatus.SOCKET_CLOSED == self.socketState:
            return
        self.socketState=SocketStatus.SOCKET_CLOSED
        self.acceptSocket.close()      
    def isConnected(self) :
        return self.socketState == SocketStatus.SOCKET_CONNECTED  
    def sendData(self,data):
        if not self.isConnected():            
            return
        self.acceptSocket.send(data)

    ###################################################
    #callback_method onFdRead
    ###################################################
    def onFdRead(self):        
        while True:
            try:
                data = self.acceptSocket.recv(self.recvBufSize)
                if not data:   
                    self.dumpLog("onFdRead Zero")                    
                    self.disconnect(is_release=False)
                    return                
                self.recvBuffer += data                
                readSize=self.onRead(self.recvBuffer)    
                self.recvBuffer = self.recvBuffer[readSize:]                
                pass
            except socket.error, msg:
                if msg.errno == errno.EAGAIN:
                    #print "TcpConnector onFdRead EAGAIN<linux>"
                    break
                if msg.errno == errno.EWOULDBLOCK:
                    #print "TcpConnector onFdRead EWOULDBLOCK<windows>"
                    break
                else:                   
                    #(ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
                    #(errno2, err_msg2) = ErrorValue
                    log="read error,errno:{0}".format(msg.errno )
                    self.dumpLog(log) 
                    self.disconnect(is_release=False)
                    return
    ###################################################
    #callback_method onRead
    ###################################################            
    def onRead(self,recvBuffer):        
        total_size=len(recvBuffer)
        begin_pos=0
        end_pos=total_size
        while begin_pos < end_pos:
            leftBuffer=recvBuffer[begin_pos:]
            unpack_size=self.unpackFromBuffer(leftBuffer)
            if unpack_size < 0:                
                self.dumpLog("unpackFromBuffer error") 
                self.disconnect()
                break
            if unpack_size==0:
                break
            packet=recvBuffer[begin_pos:begin_pos+unpack_size]
            self.dispatchPacket(packet)
            begin_pos += unpack_size            
        return begin_pos  

    ###################################################
    #child class must override this interface
    ###################################################     
    def unpackFromBuffer(self,leftBuffer):
        print "unpackFromBuffer:",len(leftBuffer),leftBuffer
        return len(leftBuffer)     
    
    ###################################################
    #callback_method dispatchPacket
    ###################################################  
    def dispatchPacket(self,packet):
        if not self.messageQueue:
            self.dumpLog("dispatchPacket,but self.messageQueue is None")
            return
        
        #self.dumpLog( "dispatchPacket,curentRecvQeue size:{0}".format( self.messageQueue.qsize() ))
        if self.messageQueue.qsize() > 128:
            self.dumpLog( "dispatchPacket Error,self.messageQueue.qsize() too big" )
            return
        task=self.makeTask(packet)
        self.messageQueue.put(task)
        #print "TcpConnector dispatchPacket:",packet
        pass
    ##child class must override this interface
    def makeTask(self,packet):
        return packet
    
