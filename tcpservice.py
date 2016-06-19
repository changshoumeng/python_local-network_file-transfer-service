# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng
from protocol_filetransfer import *
from tcpacceptor import *
import sys,socket,select
from TcpFrontWorker import  *
from config import *
from common import *

#################################################################
class TcpAcceptorMgr(object):
    def __init__(self,port,timeout,taskQueue):
        self.addr=('0.0.0.0', port)        
        self.timeout=timeout
        self.listenSocket=None
        self.isStart=0
        self.sessionIdSeed=0
        self.acceptorDict={}
        self.recvQueue=taskQueue
        pass
    
    def genSessionId(self):
        self.sessionIdSeed += 1
        return self.sessionIdSeed
    
    def start(self):
        print "start..."
        try:
            mkdir(CONFIG.tempdir)
            self.listenSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.listenSocket.setblocking(False)  
            self.listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listenSocket.bind(self.addr)
            self.listenSocket.listen(128)
            dump_log( " listen in {0}".format(self.addr) )
            self.isStart=1
            return True
        except:
            (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
            info= "listen failed:{0} {1} ".format( ErrorValue,self.addr)
            dump_log(info )
            self.closeListenSocket()
            self.isStart=0     
        return False
    
    def closeListenSocket(self):
        dump_log("closeListenSocket")
        if self.listenSocket :
            self.listenSocket.close()
            self.listenSocket=None

    def is_started(self):
        return self.isStart == 1    
    
    def addTcpAcceptor(self,acceptor):       
        tid=acceptor.acceptSocket.fileno()
        acceptor.sessionId=self.genSessionId()
        self.acceptorDict[tid]=acceptor
        dump_log( "addTcpAcceptor:{0}".format(tid) )
     
    def delTcpAcceptor(self,acceptor):
        tid=acceptor.acceptSocket.fileno()
        dump_log(  "delTcpAcceptor:{0}".format(tid) )
        if  tid in self.acceptorDict:
            del  self.acceptorDict[tid]    
    
    def onFdAccept(self):
        client_socket, client_address = self.listenSocket.accept()
        dump_log( 'connection from {0}'.format( client_address) )
        client_socket.setblocking(0)
        #tcpAcceptor=TcpAcceptor(0,client_socket, client_address,self.recvQueue)
        tcpAcceptor=TcpFrontWorker(0,client_socket, client_address,self.recvQueue)        
        self.addTcpAcceptor(tcpAcceptor) 
  
    def onFdRead(self,sock):
        tid=sock.fileno()
        if tid not in self.acceptorDict:
            dump_log(  "onFdRead cannot find tid:{0}".format(tid) )
            return 
        tcpAcceptor=self.acceptorDict[tid]
        tcpAcceptor.onFdRead()
        
    def getInputs(self):
        inputs  = [self.listenSocket]
        invalids=[]
        for tcpAcceptor in self.acceptorDict.values():              
            if not tcpAcceptor.isConnected():
                invalids.append(tcpAcceptor)                
                continue
            acceptSocket=tcpAcceptor.acceptSocket         
            inputs.append(acceptSocket)
        for tcpAcceptor in  invalids:            
            self.delTcpAcceptor(tcpAcceptor)
            tcpAcceptor.disconnect()
        return    inputs          
                
        
    def serve_once(self):
        if not  self.is_started():
            return

        try:
            inputs  = self.getInputs()
            outputs = []
            timeout = 0.01
            readable , writable , exceptional = select.select(inputs, outputs, inputs, timeout)
            # When timeout reached , select return three empty lists
            if not (readable or writable or exceptional) :
                #print "Time out ! "
                return
            self.process_readable(readable)
            self.process_writable(writable)
            self.process_exceptional(exceptional)
        except:
            print "serve_once except:"
            
    def process_readable(self,readable):
        for sock in readable :
            if sock is self.listenSocket:
                self.onFdAccept()
            else:
                self.onFdRead(sock)
                
    def process_writable(self,writable):
        pass
        '''
        for sock in writable:  
            try:  
                next_msg = message_queues[s].get_nowait()  
            except Queue.Empty:  
                print >>sys.stderr, '  ', s.getpeername(), 'queue empty'  
                outputs.remove(s)  
            else:  
                print >>sys.stderr, '  sending "%s" to %s' % \  
                    (next_msg, s.getpeername())  
                s.send(next_msg)  
        '''    
    def process_exceptional(self,exceptional):
        pass
        """
        if self.clientSocket in exceptional:
            print " exception condition on "
            self.disconnect()
        pass
        """

if __name__ == '__main__':
    print __file__
    tcpServ=TcpAcceptorMgr(1989,1)
    tcpServ.start()
    while True:
        time.sleep(0.01)
        tcpServ.serve_once()
    
    
    
    
            
                            