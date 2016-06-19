# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng

from TcpClient import *
from protocol_filetransfer import *
import json
import  traceback
import time
import Queue
import os,sys
from fileTransferContext import  *
from common import *
from config import *

class FileTransferClient(FileTransferContext):
    def __init__(self,ip,port,filePath):
        super(FileTransferClient, self).__init__()
        self.messageQueue=Queue.Queue()
        self.tcpClient = TcpClient(0, ip,port, self.messageQueue)
        self.transferType = FileTransferContext.TRANSFER_TYPE_RECV
        self.filePath = filePath
        self.fileBaseName = os.path.basename(self.filePath)
        self.fileChunkSize = COMMON.PACKET_BODY_SIZE
        self.tmpdir=CONFIG.client_tmpdir
        pass

    def start(self):
        mkdir(self.tmpdir)
        isOK = self.tcpClient.start()
        if isOK :
            self.sendFileDownloadReq()
            return True
        else:
            print "fileClient start filed:",self.filePath
            return False

    def stop(self):
        self.tcpClient.disconnect()
        self.finiTransInfo()

    def isRunOk(self):
         return self.tcpClient.isConnected()


   #>>REQ
    def sendFileDownloadReq(self):
        req = FILE_TRANSFER_PACKET()
        req.muCmd = FILE_CMD.CMD_FILE_DOWNLOAD_REQ
        body = dict()
        body["fileName"] = self.filePath
        body_str = json.dumps(body)
        req.body = body_str
        req.muSize = req.getSize()
        self.tcpClient.sendPacket(req)
        print ">>will download {0}".format(body_str)

    #<<RSP
    def onFileDownloadRsp(self,rsp):
        #rsp = FILE_TRANSFER_PACKET()
        if rsp.muMsgId == 0:
            print "<<onFileDownloadRsp ,rsp failed: cmd:{0} size:{1}".format(rsp.muCmd,rsp.muSize)
            return
        self.transferMsgId=rsp.muMsgId
        self.fileTotalSize=rsp.mu32BitField
        if self.fileTotalSize == 0:
            print "cannot find file:{0} from server".format(self.filePath)
            return
        self.fileBaseName=os.path.basename(self.filePath)
        self.initTransferInfo()
        self.transferSeqNum=0
        self.transferedSize=0
        self.sendFileDownReceipt()

    # >>REQ
    def sendFileDownReceipt(self):
        req = FILE_TRANSFER_PACKET()
        req.muCmd = FILE_CMD.CMD_FILE_SEGMENT_DOWNLOAD_RECIPT
        req.muSeqnum=self.transferSeqNum
        req.muMsgId = self.transferMsgId
        req.muSize = req.getSize()
        self.tcpClient.sendPacket(req)

    # <<RSP
    def onFileSegmentDownloadRsp(self,rsp):
        if rsp.muMsgId != self.transferMsgId:
            print "uploadrsp error msgid_no_math cli-msgid:{0} svr-msgid:{1}".format(self.transferMsgId,rsp.muMsgId)
            return
        self.writeBuffer(rsp.body)
        self.transferSeqNum = rsp.muSeqnum
        self.traceTransferInfo()
        if self.isFinished():
            print "finished"
            pass
        else:
            self.sendFileDownReceipt()

    def serve_once(self):
        try:
            self.tcpClient.serve_once()
            next_msg = self.messageQueue.get_nowait()
            self.OnProcessPacket(next_msg)
        except Queue.Empty:
            #print 'queue empty'
            pass
        pass

    def OnProcessPacket(self,packet_data):
        rsp = FILE_TRANSFER_PACKET()
        rsp.unpack(packet_data)
        if rsp.muCmd == FILE_CMD.CMD_FILE_DOWNLOAD_RSP:
            self.onFileDownloadRsp(rsp)
            return
        if rsp.muCmd == FILE_CMD.CMD_FILE_SEGMENT_DOWNLOAD_NOTIFY:
            self.onFileSegmentDownloadRsp(rsp)


def main():
    if len(sys.argv) != 2:
        print "usage: python {0} filename".format(__file__)
        return
    ip=CONFIG.server_ip
    port = CONFIG.server_port
    fn=sys.argv[1]
    if not os.path.exists(fn):
        print "cannot find file:",fn
        return
    f = FileTransferClient(ip,port,fn)
    isOK = f.start()
    if isOK == False:
        print "start failed,fn:{0}".format(fn)
        return
    while True:
        if f.isFinished():
            print "------------finished----------------"
            print "you can see:",f.tmpdir
            time.sleep(0.1)
            break
        f.serve_once()
        if f.isRunOk():
            time.sleep(0.001)
        else:
            time.sleep(2)
    f.stop()
    print "----system exit----"
    pass

if __name__ == "__main__":
    print  __file__
    main()
