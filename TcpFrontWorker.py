# -*- coding: utf-8 -*-
# Give wisdom to the machine,By ChangShouMeng
from protocol_filetransfer import *
from tcpacceptor import *
import os
import json
import traceback
from config import *
from common import *
from fileTransferContext import  *

class TcpFrontWorker(TcpAcceptor):
    def __init__(self, serverType, acceptSocket, acceptAddr, msgQueue=None):
        super(TcpFrontWorker, self).__init__(serverType, acceptSocket, acceptAddr, msgQueue)
        self.msgSeedId=0

    def genMsgId(self):
        self.msgSeedId += 1
        return self.msgSeedId

    # How unpack a packet from buffer
    def unpackFromBuffer(self, leftBuffer):
        leftSize = len(leftBuffer)
        if leftSize < FILE_TRANSFER_HEAD.getSize():
            return 0
        net_head_data = leftBuffer[0:FILE_TRANSFER_HEAD.getSize()]
        net_head = FILE_TRANSFER_HEAD()
        net_head.unpack(net_head_data)
        if net_head.muSize > COMMON.MAX_PACKET_SIZE or net_head.muSize < COMMON.MIN_PACKET_SIZE:
            dump_log( "[TcpClient] unpackFromBuffer packetSize:{0} error:".format(net_head.muSize) )
            return -1
        if leftSize < net_head.muSize:
            return 0
        return net_head.muSize
        pass

    # pack a data to packet then send out
    def sendPacket(self, packet):
        data = packet.pack()
        self.sendData(data)

    # how to dispatch packet to different worker
    def dispatchPacket(self, packet):
        req = FILE_TRANSFER_PACKET()
        req.unpack(packet)
        if req.muCmd == FILE_CMD.CMD_FILE_UPLOAD_REQ:
            self.onFileUploadReq(req)
        elif req.muCmd == FILE_CMD.CMD_FILE_SEGMENT_UPLOAD_REQ:
            self.onFileSegmentUploadReq(req)
        elif req.muCmd == FILE_CMD.CMD_FILE_DOWNLOAD_REQ:
            self.onFileDownloadReq(req)
        elif req.muCmd == FILE_CMD.CMD_FILE_SEGMENT_DOWNLOAD_RECIPT:
            self.onFileSegmentDownReciept(req)
            pass
        pass

    def onFileUploadReq(self, req):
        j_str = req.body
        dump_log( "uploadreq:{0}".format( j_str) )
        try:
            j = json.loads(j_str)
            self.fileTransferContext = FileTransferContext()
            self.fileTransferContext.transferType = FileTransferContext.TRANSFER_TYPE_RECV
            self.fileTransferContext.tmpdir = CONFIG.tempdir
            self.fileTransferContext.fileBaseName=j["fileName"]
            self.fileTransferContext.fileTotalSize=j["fileSize"]
            if  self.fileTransferContext.fileTotalSize == 0:
                req.muCmd = FILE_CMD.CMD_FILE_UPLOAD_RSP
                req.muMsgId = 0
                req.body = '{"msg":"file size 0 "}'
                req.muSize = req.getSize()
                self.sendPacket(req)
                dump_log("recv file size 0")
                return
            if self.fileTransferContext.workStatus ==1 :
                req.muCmd= FILE_CMD.CMD_FILE_UPLOAD_RSP
                req.muMsgId = 0
                req.body='{"msg":"is busy"}'
                req.muSize = req.getSize()
                self.sendPacket(req)
                dump_log("current session is busy,please wait")
                return
            self.fileTransferContext.initTransferInfo()
            req.muCmd = FILE_CMD.CMD_FILE_UPLOAD_RSP
            req.muMsgId = self.genMsgId()
            req.muSize=req.getSize()
            self.sendPacket(req)
            self.fileTransferContext.transferMsgId = req.muMsgId
            dump_log("uploadrsp:msgid:{0}".format(req.muMsgId ))
            pass
        except:
            print "onFileUploadReq except:",traceback.print_exc()
            pass

        pass

    def onFileSegmentUploadReq(self,req):
        if req.muMsgId != self.fileTransferContext.transferMsgId:
            dump_log("data req error -> msgid_no_math cli-msgid:{0} svr-msgid:{1} ".format( req.muMsgId,self.fileTransferContext.transferMsgId  )   )
            return
        if req.muSeqnum != self.fileTransferContext.transferSeqNum + 1:
            dump_log("data req error -> seqn_no_math msgid:{0} cli-seq:{1} svr-seq:{2}".format(req.muMsgId,req.muSeqnum, self.fileTransferContext.transferSeqNum+1 ))
            return
        if len(req.body) == 0:
            print "data req error,body empty"
            return
        try:
            self.fileTransferContext.writeBuffer(req.body)
            rsp = FILE_TRANSFER_PACKET()
            rsp.muCmd = FILE_CMD.CMD_FILE_SEGMENT_UPLOAD_RSP
            rsp.mu32BitField = len(req.body)
            rsp.muMsgId = req.muMsgId
            rsp.muSeqnum = req.muSeqnum
            rsp.muSize = rsp.getSize()
            self.sendPacket(rsp)
            self.fileTransferContext.transferSeqNum  = req.muSeqnum
            if self.fileTransferContext.isFinished():
                self.fileTransferContext.finiTransInfo()
                print " --------recv finished -----------"
            else:
                self.fileTransferContext.traceTransferInfo()
            pass

        except:
            pass

    def onFileDownloadReq(self,req):
        j_str = req.body
        dump_log("downloadreq:{0}".format(j_str))
        try:
            j = json.loads(j_str)
            self.fileTransferContext = FileTransferContext()
            self.fileTransferContext.transferType = FileTransferContext.TRANSFER_TYPE_SEND
            self.fileTransferContext.tmpdir = CONFIG.tempdir
            self.fileTransferContext.fileChunkSize=COMMON.PACKET_BODY_SIZE
            fileName=j["fileName"]
            fileBaseName=os.path.basename(fileName)
            if fileName == fileBaseName:
                filePath=r'{0}/{1}'.format(self.fileTransferContext.tmpdir,fileBaseName)
            else:
                filePath=fileName
            self.fileTransferContext.filePath=filePath
            print "filePath:",filePath
            if False==os.path.exists(filePath) or False==self.fileTransferContext.initTransferInfo():
                rsp = FILE_TRANSFER_PACKET()
                rsp.muCmd = FILE_CMD.CMD_FILE_DOWNLOAD_RSP
                rsp.muMsgId = 0
                rsp.mu32BitField = 0
                rsp.muSize = rsp.getSize()
                self.sendPacket(rsp)
                dump_log( "download req error,cannot find file:{0}".format(filePath) )
                dump_log( "current dir is:{0} ; current file is:{1}".format(os.path.curdir,__file__) )
                return
            rsp = FILE_TRANSFER_PACKET()
            rsp.muCmd = FILE_CMD.CMD_FILE_DOWNLOAD_RSP
            rsp.muMsgId = self.genMsgId()
            rsp.mu32BitField = self.fileTransferContext.fileTotalSize
            rsp.muSize = rsp.getSize()
            self.sendPacket(rsp)
            self.fileTransferContext.transferMsgId = rsp.muMsgId
        except:
            print "onFileDownloadReq except:", traceback.print_exc()
        pass
    def onFileSegmentDownReciept(self,req):
        if req.muMsgId != self.fileTransferContext.transferMsgId:
            dump_log("msgid_not_match cli-msgid:{0} svr-msgid:{1}".format( req.muMsgId,self.fileTransferContext.transferMsgId) )
            return
        if req.muSeqnum != self.fileTransferContext.transferSeqNum:
            dump_log("seqnum_not_match cli-seqnum:{0} svr-seqnum:{1}".format( req.muSeqnum,self.fileTransferContext.transferSeqNum) )
            return
        rsp = FILE_TRANSFER_PACKET()
        rsp.muMsgId = self.fileTransferContext.transferMsgId
        rsp.muCmd = FILE_CMD.CMD_FILE_SEGMENT_DOWNLOAD_NOTIFY
        rsp.muSeqnum = self.fileTransferContext.transferSeqNum+1
        rsp.body = self.fileTransferContext.readBuffer()
        self.fileTransferContext.transferedSize += len(rsp.body)
        self.fileTransferContext.traceTransferInfo()
        if len( rsp.body )  == 0:
            self.fileTransferContext.finiTransInfo()
            print "--------send over-----------"
            return
        rsp.muSize = rsp.getSize()
        self.sendPacket(rsp)
        self.fileTransferContext.transferSeqNum= rsp.muSeqnum
        pass