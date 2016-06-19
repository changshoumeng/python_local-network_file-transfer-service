import fcntl


def syncWriteLine(fileName,data):
        fp=None
        try:
                fp=open(fileName,'a+')
                fcntl.flock(fp,fcntl.LOCK_EX)
                fp.write(data+"\n")    
        finally:
                if fp != None:
                        fcntl.flock(fp,fcntl.LOCK_UN)
                        fp.close()
