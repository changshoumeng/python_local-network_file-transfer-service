# -*- coding: utf-8 -*-
import socket 
import traceback
import sys
import select,errno
import Queue
import time
socket.setdefaulttimeout(2)
from common import *



class TcpConnector(object):
    def __init__(self,connType,ip,port,messageQueue=None):
        self.ip=ip
        self.port=port
        self.addr=(self.ip,self.port)  
        self.connType=connType
        self.clientSocket=None
        self.connState=0
        self.workState=0
        self.connTimeoutCount=0
        self.messageQueue=messageQueue
        self.recvBuffer=""
        self.recvBufSize=1024
        self.serveTime= getNowTime()
        pass
    
    def start(self):
        isOK=self.connect()
        if isOK:
            self.workState=1
        else:
            self.workState=0
        return isOK
    
    def connect(self):                
        self.clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)        
        try:
            self.clientSocket.connect(self.addr)
            self.connState=1
            print "TcpConnector connect succ:",self.addr
            self.clientSocket.setblocking(False)            
            return True
        except:
            (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
            print "Connect server failed: ", ErrorValue,self.addr
            self.connState=0
            self.clientSocket.close()
        sys.stdout.flush()    
        return False
    
    def disconnect(self):
        print "TcpConnector[{0}] disconnect self.connState:{1}".format(self.addr,self.connState)
        if self.connState == 0:
            return        
        self.clientSocket.close()
        self.connState=0
    
    def isConnected(self) :
        return self.connState == 1
    
    def sendData(self,data):
        if self.connState == 0:
            print "sendData error,conenctor is disconnected"
            return
        self.clientSocket.send(data)
    
    def keepConnectState(self):
        if 1 != self.workState :
            return False
        if 1 != self.connState :
            return False
            if self.connTimeoutCount <3:
                self.connTimeoutCount += 1                
            else:
                self.connTimeoutCount = 0
                self.connect()
            return False  
        return  True
    
    def serve_once(self):
        if False == self.keepConnectState():
            print "serve_once not-connect ", self.addr
            return
        
        nowTime= getNowTime()
        if nowTime > self.serveTime + 10:
            self.keepAlive()
            self.serveTime = nowTime
            pass             
        
        #sockets from which we except to read
        inputs = [self.clientSocket]       
        #sockets from which we expect to write
        outputs = []        
        #Outgoing message queues (socket:Queue)
        message_queues = {}        
        #A optional parameter for select is TIMEOUT
        timeout = 0.01
        readable , writable , exceptional = select.select(inputs, outputs, inputs, timeout)
        # When timeout reached , select return three empty lists
        if not (readable or writable or exceptional) :
            #print "Time out ! "
            return           
        if self.clientSocket in readable :      
            self.onFdRead()
        if self.clientSocket in exceptional:
            print " exception condition on "
            self.disconnect()
                 
    def onFdRead(self):
        #print "onFdRead-----------------------------------"
        while True:
            try:
                data = self.clientSocket.recv(self.recvBufSize)
                if not data:
                    print "TcpConnector[{0}] onFdRead Zero".format(self.addr)
                    self.disconnect()
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
                    (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
                    (errno2, err_msg2) = ErrorValue
                    print "TcpConnector onFdRead error:",msg.errno,self.addr,errno2,err_msg2
                    self.disconnect()
                    return                         

        
        
    def onRead(self,recvBuffer):        
        total_size=len(recvBuffer)
        begin_pos=0
        end_pos=total_size
        while begin_pos < end_pos:
            leftBuffer=recvBuffer[begin_pos:]
            unpack_size=self.unpackFromBuffer(leftBuffer)
            if unpack_size < 0:
                print "TcpConnector unpackFromBuffer error"
                self.disconnect()
                break
            if unpack_size==0:
                break
            packet=recvBuffer[begin_pos:begin_pos+unpack_size]
            self.dispatchPacket(packet)
            begin_pos += unpack_size            
        return begin_pos

    ##
    def dispatchPacket(self,packet):
        if not  self.messageQueue:
            return
        #print "dispatchPacket,curentRecvQeue size:",self.messageQueue.qsize()
        if self.messageQueue.qsize() > 128:
            print "dispatchPacket Error,self.messageQueue.qsize() too big"
            return
        task=self.makeTask(packet)
        self.messageQueue.put(task)
        #print "TcpConnector dispatchPacket:",packet
        pass
    
    ##child class must override this interface
    def makeTask(self,packet):
        return packet
        
    ##child class must override this interface
    def unpackFromBuffer(self,leftBuffer):
        print "TcpConnector unpackFromBuffer:",len(leftBuffer)
        return len(leftBuffer)
        pass
     ##child class must override this interface
    def keepAlive(self):
        print "TcpConnector keepAlive:"
        pass
        
 