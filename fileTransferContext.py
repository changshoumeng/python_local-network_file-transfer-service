# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng\
#定义传输的上下文，client与server通用的上下文
import time
import os,sys,traceback

class FileTransferContext(object):
    TRANSFER_TYPE_SEND=0
    TRANSFER_TYPE_RECV=1
    def __init__(self):
        self.transferType=0
        self.filePath = ""  # absolute path,send
        self.fileTotalSize = 0
        self.fileChunkSize=1024
        self.contextName="-"
        self.fileBaseName=""#only filename,recv
        self.fileHandle = None
        self.transferedSize=0
        self.transferMsgId = 0
        self.transferSeqNum = 0
        self.transferSeqNumUpLimit = 0
        self.transferSeqChunkSize = 10
        self.transferBeginTime = 0
        self.tmpdir="temp"
        self.workStatus=0

    def __del__(self):
        self.finiTransInfo()

    def initTransferInfo(self):
        print "---begin----init transfer info"
        try:
            if  self.transferType== FileTransferContext.TRANSFER_TYPE_SEND:
                self.contextName="snd>>"
                self.fileTotalSize = os.path.getsize(self.filePath)
                self.fileBaseName = os.path.basename(self.filePath)
                self.fileHandle=open(self.filePath,'rb')
            else:
                self.contextName="rcv<<"
                tmp_fn = r"{0}/{1}_tmp".format(self.tmpdir, self.fileBaseName)
                self.fileHandle=open(tmp_fn,'wb')
                print tmp_fn
                assert self.fileHandle
            self.transferBeginTime= (int)(time.time())
            self.transferedSize=0
            self.transferSeqNumUpLimit=self.fileTotalSize/self.fileChunkSize + 1
            self.workStatus=1
            print "initTransferInfo {0} fileName:{1} fileSize:{2} fileChunkSize:{3}".format(self.contextName,self.fileBaseName,self.fileTotalSize,self.fileChunkSize)
            return True
        except:
            print "initTransferinfo failed:",traceback.print_exc()
            print "init filepath is:",self.filePath
        return False

    def  finiTransInfo(self):
        if not self.fileHandle:
            return
        try:
            if self.transferType == FileTransferContext.TRANSFER_TYPE_RECV:
                self.fileHandle.flush()
            self.fileHandle.close()
            self.fileHandle=None
        except:
            print "finiTransInfo failed:", traceback.print_exc()


    def traceTransferInfo(self):
        if self.transferedSize == self.fileTotalSize:
            self.workStatus=2
        if self.transferSeqNum > 5 and (self.transferSeqNum % self.transferSeqChunkSize) != 0:
            return
        useTime  = int(time.time()) - self.transferBeginTime
        speed = ""
        progress = float(self.transferedSize) / float(self.fileTotalSize)
        if useTime > 0:
             speedint = float(self.transferedSize) / float(useTime * 1024)
             if speedint >= 1024:
                 speedint=  float(speedint)/ float(1024)
                 speed="{:.2f}mb/s".format(speedint)
             else:
                 speed="{:.2f}kb/s".format(speedint)
             pass
        print "{0}msgid:{1} total:{2}byte tranfered:{3}byte speed:{4} progress:{5:.2f} use-time:{6}s".format(
            self.contextName,
            self.transferMsgId,
            self.fileTotalSize,
            self.transferedSize,
            speed,
            progress,
            useTime)


    def readBuffer(self):
        try:
            return self.fileHandle.read(self.fileChunkSize)
        except:
            print "readBuffer err:",traceback.print_exc()
        return ""

    def writeBuffer(self,buffer):
        try:
            self.fileHandle.write(buffer)
            if (self.transferSeqNum % self.transferSeqChunkSize) == 0:
                self.fileHandle.flush()
            self.transferedSize += len(buffer)
           #print self.transferedSize,self.fileTotalSize
            if self.transferedSize == self.fileTotalSize:
                self.fileHandle.flush()
                self.fileHandle.close()
                self.fileHandle=None
                tmp_fn = "{0}/{1}_tmp".format(self.tmpdir, self.fileBaseName)
                real_fn = "{0}/{1}".format(self.tmpdir, self.fileBaseName)
                print "-"*80
                print "tmp_fn:",tmp_fn
                print "real_fn:",real_fn
                if os.path.exists(real_fn):
                    os.remove(real_fn)
                os.rename(tmp_fn,real_fn)
                self.workStatus=2
        except:
            print "writeBuffer err:",traceback.print_exc()
        return

    def isFinished(self):
        if self.workStatus <= 1:
            return False
        return True

