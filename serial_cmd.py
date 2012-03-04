#! /usr/bin/python

"""
    This module is used to communicate with serial port.
It listens to certain port to receiving commands, then
translates to serial port.
"""

import sys
import time
import Queue 
import socket
import getopt
import serial
import os.path
import threading

is_stopped = False;

class TestThreadClass(threading.Thread):
    def send_data(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect("/tmp/test_unix_sock")
        s.send("Hello, world.")
        s.close()

    def run(self):
        self.send_data()
        time.sleep(1)
        self.send_data()
        time.sleep(2)
        self.send_data()
        time.sleep(4)

class KeyboardListenThreadClass(threading.Thread):
    def __init__(self, finish_func):
        threading.Thread.__init__(self)
        self._fin_func = finish_func

    def run(self):
        global is_stopped 
        print ("Press Q to Exist")
        while (True):
            key = raw_input()
            if key == "Q":
                is_stopped = True;
                self._fin_func()
                break;

class UnixDomainCommandParser(threading.Thread):
    def __init__(self, file_name, sock_type = socket.SOCK_STREAM): 
        threading.Thread.__init__(self)
        self._file_name = file_name
        self._sock_type = sock_type

    def run(self): 
        global is_stopped
        s = socket.socket(socket.AF_UNIX, self._sock_type)
        self.queue = Queue.Queue()
        if os.path.exists(self._file_name):
            try:
                os.remove(self._file_name)
            except OSError:
                pass
        s.bind(self._file_name)
        while (not is_stopped):
            s.listen(1)
            conn, addr = s.accept()
            data = conn.recv(1024)
            if not data:
                break
            print ("%s is received") % (data)
            self.queue.put(data)
            conn.close()
            print ("conn is closed")

    def get_cmd(self):
        return self.queue.get()

    def finish(self):
        self.queue.put("")
        fin = socket.socket(socket.AF_UNIX, self._sock_type)
        fin.connect(self._file_name)
        fin.close()

def serial_serv(tty, baud):
    try:
        ser = serial.Serial(tty, baud)
    except serial.serialutil.SerialException:
        print ("failed to open: %s@%d") % (tty, baud)
        return
    except IOError:
        print ("IOError to open: %s@%d") % (tty, baud)
        return
    global is_stopped
    cp = UnixDomainCommandParser("/tmp/test_unix_sock")
    cp.start()

    time.sleep(1)
    t = KeyboardListenThreadClass(cp.finish)
    t.start()

# test block start 
    test = TestThreadClass()
    test.start()
# test block end

    time.sleep(1);
    while (not is_stopped):
        cmd = cp.get_cmd();
        if not cmd == "":
            print ("I'm running %s") % (cmd)

    t.join()
    cp.join()
    test.join()
    ser.close()

def main():
    tty = None
    baud = 0
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:b:", ["help","tty=","baud="])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)

    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        elif o in ("-s", "--tty"):
            tty = a
            print "open tty: %s" % (tty)
        elif o in ("-b", "--baud"):
            baud = int(a)
            print "baud rate: %d" % (baud)

    if tty is None:
        print "%s is null" % (tty)
        sys.exit(2)
    elif not os.path.exists(tty):
        print "%s does not exist" % (tty)
        sys.exit(2)
    elif baud <= 0:
        print "baud rate is invalid"
        sys.exit(2)
    serial_serv(tty, baud)

if __name__ == "__main__":
    main()

