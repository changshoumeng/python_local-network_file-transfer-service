# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng

from TcpClient import *
from protocol_filetransfer import *
import json
import Queue
from fileTransferContext import  *
from config import *

class FileTransferClient(FileTransferContext):
    def __init__(self,ip,port,filePath):
        super(FileTransferClient, self).__init__()
        self.messageQueue=Queue.Queue()
        self.tcpClient = TcpClient(0, ip,port, self.messageQueue)
        self.transferType = FileTransferContext.TRANSFER_TYPE_SEND
        self.filePath = filePath
        self.fileBaseName = os.path.basename(self.filePath)
        self.fileChunkSize = COMMON.PACKET_BODY_SIZE
        pass

    def start(self):
        if not  self.initTransferInfo():
            return False
        isOK = self.tcpClient.start()
        if isOK :
            self.sendFileUploadReq()
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
    def sendFileUploadReq(self):
        req = FILE_TRANSFER_PACKET()
        req.muCmd = FILE_CMD.CMD_FILE_UPLOAD_REQ
        req.mu32BitField = CONFIG.max_body_size
        body = dict()
        body["fileName"] = self.fileBaseName
        body["fileSize"] = self.fileTotalSize
        body_str = json.dumps(body)
        req.body = body_str
        req.muSize = req.getSize()
        self.tcpClient.sendPacket(req)
        print ">>will upload {0}".format(body_str)

    #<<RSP
    def onFileUploadRsp(self,rsp):
        #rsp = FILE_TRANSFER_PACKET()
        if rsp.muMsgId == 0:
            print "<<onFileUploadRsp ,rsp failed: cmd:{0} size:{1}".format(rsp.muCmd,rsp.muSize)
            return
        self.transferMsgId=rsp.muMsgId
        self.transferSeqNum=1
        self.transferedSize=0
        self.sendFileSegmentUploadReq()

    #>>REQ
    def sendFileSegmentUploadReq(self):
        buffer=self.readBuffer()
        if len(buffer) == 0:
            return
        req = FILE_TRANSFER_PACKET()
        req.muCmd = FILE_CMD.CMD_FILE_SEGMENT_UPLOAD_REQ
        req.muMsgId = self.transferMsgId
        req.mu32BitField = len(buffer)
        req.muSeqnum = self.transferSeqNum
        req.body=buffer
        req.muSize = req.getSize()
        self.tcpClient.sendPacket(req)

    # <<RSP
    def onFileSegmentUploadRsp(self,rsp):
        if rsp.muMsgId != self.transferMsgId:
            print "uploadrsp error msgid_no_math cli-msgid:{0} svr-msgid:{1}".format(self.transferMsgId,rsp.muMsgId)
            return
        if rsp.muSeqnum != self.transferSeqNum:
            print "uploadrsp error seqN_no_math cli_seq:{0} svr_seq:{1}".format(self.transferSeqNum,rsp.muSeqnum)
            return
        self.transferedSize += rsp.mu32BitField
        self.transferSeqNum += 1
        self.traceTransferInfo()
        self.sendFileSegmentUploadReq()

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
        if rsp.muCmd == FILE_CMD.CMD_FILE_UPLOAD_RSP:
            self.onFileUploadRsp(rsp)
            return
        if rsp.muCmd == FILE_CMD.CMD_FILE_SEGMENT_UPLOAD_RSP:
            self.onFileSegmentUploadRsp(rsp)


def main():
    if len(sys.argv) != 2:
        print "usage: python {0} filename".format(__file__)
        return
    ip=CONFIG.server_ip
    port =CONFIG.server_port
    fn=sys.argv[1]
    if not os.path.exists(fn):
        print "cannot find file:",fn
        return
    f = FileTransferClient(ip,port, fn)
    isOK = f.start()
    if isOK == False:
        print "start failed,fn:{0}".format(fn)
        return
    while True:
        if f.isFinished():
            print "------------finished----------------"
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
