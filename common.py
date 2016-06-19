# -*- coding: utf-8 -*-
#Give wisdom to the machine,By ChangShouMeng
#Contacts is QQ:406878851
import  os
import multiprocessing as mp
import Queue
import traceback
import logging
import logging.config
import time

def getNowTime():
    t=time.time()
    return int(t)

def mkdir(path):
    # 去除左右两边的空格
    path = path.strip()
    # 去除尾部 \符号
    path = path.rstrip("\\")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


class GlobalQueue(Singleton):
    taskQueue = mp.JoinableQueue()
    logQueue = mp.JoinableQueue()

    @staticmethod
    def dumpLog(info):
        GlobalQueue.logQueue.put(info)

    # print ""

    @staticmethod
    def outputLog():

        if GlobalQueue.logQueue.qsize() == 0:
            return
        # print "outputlog:",GlobalQueue.logQueue.qsize()
        try:
            t = GlobalQueue.logQueue.get()
            print "log>>:", t
        except Queue.Empty:
            print "queue is empty"


def dump_log(info):
    print info
