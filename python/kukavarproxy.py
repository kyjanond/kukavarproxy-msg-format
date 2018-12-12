import socket                                                   # Used for TCP/IP communication
import select

TIMEOUT = 1

class KUKAException(Exception):
    pass

class KUKA(object):

    def __init__(self, TCP_IP):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# Initializing client connection
        self.client.settimeout(TIMEOUT)

        try: 
            self.client.connect((TCP_IP, 7000))                      # Open socket. kukavarproxy actively listens on TCP port 7000
        except Exception as e:
            self.error_list(1)


    def send (self, var, val, msgID):
    	"""
        kukavarproxy message format is 
        msg ID in HEX                       2 bytes
        msg length in HEX                   2 bytes
        read (0) or write (1)               1 byte
        variable name length in HEX         2 bytes
        variable name in ASCII              # bytes
        variable value length in HEX        2 bytes
        variable value in ASCII             # bytes
        """
        try:
            msg = bytearray()
            temp = bytearray()
            if val != "":
                val = str(val)
                msg.append((len(val) & 0xff00) >> 8)            # MSB of variable value length
                msg.append((len(val) & 0x00ff))                 # LSB of variable value length
                msg.extend(map(ord, val))                       # Variable value in ASCII
            temp.append(bool(val))                              # Read (0) or Write (1)
            temp.append(((len(var)) & 0xff00) >> 8)             # MSB of variable name length
            temp.append((len(var)) & 0x00ff)                    # LSB of variable name length
            temp.extend(map(ord, var))                          # Variable name in ASCII 
            msg = temp + msg
            del temp[:]
            temp.append((msgID & 0xff00) >> 8)                  # MSB of message ID
            temp.append(msgID & 0x00ff)                         # LSB of message ID
            temp.append((len(msg) & 0xff00) >> 8)               # MSB of message length
            temp.append((len(msg) & 0x00ff))                    # LSB of message length
            msg = temp + msg
        except Exception as e:
            raise e
            self.error_list(2)
        try:
            self.client.send(msg)
            recv_msg = self.client.recv(1024)
            return  recv_msg                           # Return response with buffer size of 1024 bytes
        except Exception as e:
            raise e
            self.error_list(1)


    def __get_var(self, msg):
        """
        kukavarproxy response format is 
        msg ID in HEX                       2 bytes
        msg length in HEX                   2 bytes
        read (0) or write (1)               1 byte
        variable value length in HEX        2 bytes
        variable value in ASCII             # bytes
        Not sure if the following bytes contain the client number, or they're just check bytes. I'll check later.
        """
        try:
            # Python 2.x
            lsb = (int (str(msg[5]).encode('hex'),16))
            msb = (int (str(msg[6]).encode('hex'),16))
            lenValue = (lsb <<8 | msb)
            return msg [7: 7+lenValue]

            """
            # Python 3.x
            lsb = int( msg[5])
            msb = int( msg[6])
            lenValue = (lsb <<8 | msb)
            return str(msg [7: 7+lenValue],'utf-8')  
            """

        except Exception as e:
            raise e
            self.error_list(2)

    def read (self, var, msgID=0):
        try:
            return self.__get_var(self.send(var,"",msgID))  
        except Exception as e:
            raise e
            self.error_list(2)


    def write (self, var, val, msgID=0):
        try:
            if val != (""): return self.__get_var(self.send(var,val,msgID))
            else: raise self.error_list(3)
        except :
            self.error_list(2)


    def disconnect (self):
        print "disconnecting"    
        self.client.close()                                      # CLose socket


    def error_list (self, ID, e=Exception()):
        if ID == 1:
            #print ("Network Error (tcp_error)")
            #print ("    Check your KRC's IP address on the network, and make sure kukaproxyvar is running.")
            self.disconnect()
            raise KUKAException("Network Error (TCP_error)")
        elif ID == 2:
            #print ("Python Error.")
            #print ("    Check the code and uncomment the lines related to your python version.")
            self.disconnect()
            raise KUKAException("Python Error.")
        elif ID == 3:
            print ("Error in write() statement. Variable value is not defined.")
