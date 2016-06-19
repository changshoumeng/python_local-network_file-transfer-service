# -*- coding: utf-8 -*-
#!/usr/bin/env python
# define protocol

import struct

class STRING_DATA(object):
    def __init__(self, string=""):
        self.string = string

    def pack(self):
        length = len(self.string)
        formatStr = "%ds" % (length)
        data = struct.pack(formatStr, self.string)
        return data

    def unpack(self, data):
        length = len(data)
        formatStr = "%ds" % (length)
        # print formatStr
        self.string, = struct.unpack(formatStr, data)
        return self.string

class UINT64_DATA(object):
    def __init__(self, idv=0):
        self.muId = idv  # uint64

    def pack(self):
        format_str = "Q"
        data = struct.pack(format_str, self.muId)
        return data

    def unpack(self, data):
        assert len(data) == self.getSize()
        format_str = "Q"
        self.muId, = struct.unpack(format_str, data)
        return self.muId

    @classmethod
    def getSize(cls):
        return 8

class COMMON(object):
    MAX_PACKET_SIZE = 32768
    MIN_PACKET_SIZE = 32
    PACKET_BODY_SIZE = MAX_PACKET_SIZE-MIN_PACKET_SIZE

class FILE_CMD(object):
    CMD_HEARTBEAT = 0
    CMD_FILE_UPLOAD_REQ = 1
    CMD_FILE_UPLOAD_RSP = 2
    CMD_FILE_SEGMENT_UPLOAD_REQ = 3
    CMD_FILE_SEGMENT_UPLOAD_RSP = 4
    CMD_FILE_DOWNLOAD_REQ = 5
    CMD_FILE_DOWNLOAD_RSP = 6
    CMD_FILE_SEGMENT_DOWNLOAD_NOTIFY = 7
    CMD_FILE_SEGMENT_DOWNLOAD_RECIPT = 8
    CMD_REQUEST_ERROR = 1000
    CMD_FILE_UPLOADWORK = 8000
    CMD_FILE_DOWNLOADWORK = 8001
    CMD_FILE_WORKFINISHED = 10000

class FILE_TRANSFER_HEAD(object):
    def __init__(self):
        self.muSize=0#uint32
        self.muCmd=0#uint32
        self.muMsgId=0#uint32
        self.muSeqnum=0#uint32
        self.mu32BitField=1001#uint32
        self.muId1 = 1001  # uint32
        self.muId2 = 1001  # uint32
        self.muSessionId = 1001  # uint32
    def pack(self):
        format_str="IIIIIIII"
        data=struct.pack(format_str,self.muSize,self.muCmd,self.muMsgId,self.muSeqnum,self.mu32BitField,self.muId1,self.muId2,self.muSessionId)
        return data
    def unpack(self,data):
        format_str = "IIIIIIII"
        self.muSize, self.muCmd, self.muMsgId, self.muSeqnum, self.mu32BitField, self.muId1, self.muId2, self.muSessionId = struct.unpack(format_str,data)
        pass
    @staticmethod
    def getSize():
        return 32

class FILE_TRANSFER_PACKET(FILE_TRANSFER_HEAD):
    def __init__(self):
        super(FILE_TRANSFER_PACKET,self).__init__()
        self.body=""
        pass
    def pack(self):
        super_data=super(FILE_TRANSFER_PACKET,self).pack()
        stringData=STRING_DATA(self.body).pack()
        return super_data+stringData
    def unpack(self,data):      
        super_size= FILE_TRANSFER_HEAD.getSize()
        super_data=data[0:super_size]
        stringData=data[super_size:]
        super(FILE_TRANSFER_PACKET,self).unpack(super_data)
        self.body = STRING_DATA().unpack(stringData)
    def getSize(self):
        super_size= FILE_TRANSFER_HEAD.getSize()
        return super_size+len(self.body)
    def printInfo(self):
        print "file_transfer_packet"
        print "size:",self.muSize
        print "msgid:",self.muMsgId
        print "body:",self.body
    
if __name__ == '__main__':
    print __file__
    p=FILE_TRANSFER_PACKET()
    p.muMsgId=11
    buffer="HELLOE"
    p.body = buffer
    p.muSize =  p.getSize()
    data = p.pack()

    p2 = FILE_TRANSFER_PACKET()
    p2.unpack(data)
    p2.printInfo()


    