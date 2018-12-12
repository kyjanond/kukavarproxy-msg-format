from kukavarproxy import *
import threading
import time
import Queue
import struct

#msg format (stamp[int],name[string],seq[int],msg[byte])

def parse_axis_msg(_msg):
    _msg = _msg.split(" ")
    _vals = [
    float(_msg[2][:-1]),
    float(_msg[4][:-1]),
    float(_msg[6][:-1]),
    float(_msg[8][:-1]),
    float(_msg[10][:-1]),
    float(_msg[12][:-1]),
    float(_msg[14][:-1]),
    float(_msg[16][:-1]),
    float(_msg[18][:-1]),
    ]
    return [int(x*100000) for x in _vals]

def pack_axis_msg(msg):
    ret = ""
    ret += struct.pack("Q",msg[0])
    ret += msg[1]
    ret += struct.pack("I",msg[2])
    ret += struct.pack("9i",*msg[3])
    return ret

class Logger(threading.Thread):
    def __init__(self,path,stop_event,msg_queue,name=None):
        self.path = _path
        self.stop_event = stop_event
        self.queue = msg_queue

        super(Logger, self).__init__(name=name)
    
    def run(self):
        try:
            with open(self.path,"a") as f:
                while not self.stop_event.is_set():
                    try:
                        msg = self.queue.get(True,1)
                    except Queue.Empty:
                        continue
                    f.write(msg)
        finally:
            self.cleanup()
    def cleanup(self):
        pass


class KUKA_wrapper(threading.Thread):
    def __init__(self,ip_addr,stop_event,msg_cond,freq=25,name=None):
        self.stop_event = stop_event
        self.msg_cond = msg_cond
        self.msg = (0,name,-1,"")
        self.wait = 1.0/freq
        self.msg_seq = 0
        self.ip_addr = ip_addr
        self.KUKA = None

        super(KUKA_wrapper, self).__init__(name="{:>8}".format(name))

    
    def run(self):
        print self.name+" starting" 
        while not self.stop_event.is_set():
            while not self.stop_event.is_set():
                try:
                    self.KUKA = KUKA(self.ip_addr)
                    break
                except Exception as e:
                    self.cleanup()
                    print self.name,e 
                    time.sleep(15)

            print self.name+" connected" 
            end_time = time.time()
            self.msg_seq = 0
            try:
                while not self.stop_event.is_set():
                    start_time = end_time
                    msg = self.KUKA.read("$AXIS_ACT")
                    msg = (time.time(),self.name,self.msg_seq,msg)
                    with self.msg_cond:
                        self.msg = msg
                        self.msg_cond.notify_all()
                    self.msg_seq+=1
                    end_time = time.time()
                    sleep_time = start_time+self.wait-end_time
                    if sleep_time>0:
                        time.sleep(start_time+self.wait-end_time)
                    else:
                        print self.name + ": " + str(sleep_time)
            finally:
                self.cleanup()

    def cleanup(self):
        if self.KUKA:
            self.KUKA.disconnect()
            print self.name+" disconnected"
            self.KUKA = None
        print self.name+" stopping" 

def main():
    msg_queue = Queue.Queue(100)
    stop_event = threading.Event()
    stop_event.clear()
    rob1_cond = threading.Condition()
    rob2_cond = threading.Condition()
    robot1 = KUKA_wrapper('192.168.2.2',stop_event,rob1_cond,10,name="PINP")
    robot2 = KUKA_wrapper('192.168.2.3',stop_event,rob2_cond,10,name="GNM")

    try:
        robot1.start()
        robot2.start()
        old_seq1 = -1
        old_seq2 = -1
        while True:
            with rob1_cond:
                rob1_cond.wait(0.01)
                msg1 = robot1.msg
            with rob2_cond:
                rob2_cond.wait(0.01)
                msg2 = robot2.msg
            if msg1[2] > old_seq1:
                parsed_msg = parse_axis_msg(msg1[3])
                msg1 = list(msg1)
                #print parsed_msg
                msg1[3] = parsed_msg
                pack_axis_msg(msg1)
                pass
            if msg2[2] > old_seq2:
                parsed_msg = parse_axis_msg(msg2[3])
                pass
            old_seq1 = msg1[2]
            old_seq2 = msg2[2]



    except KeyboardInterrupt:
        print "intrrupted. exiting now"
    finally:
        stop_event.set()
        robot1.join()
        robot2.join()

if __name__=="__main__":
    main()


