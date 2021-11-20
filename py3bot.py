import telnetlib
import socket
import threading
import time
import re
from constants import *


class Bot(object):
    def __init__(self, username, password, host="godwars2.org", port=3000, output_all=True, botname='Bot', clientname="PYBOT"):
        self.host=host
        self.port=port
        self.username = username
        self.password = password
        self.con = None
        self.connected = False
        self.out_thread = threading.Thread(target=self.output)
        self.OUTPUT_ALL = output_all
        self.botname = botname
        self.clientname = clientname
        self.triggers = {}
        self.tempthreads = []
        self.loadstring = "load %s %s\n" % (self.username, self.password)
        self.loadstring.encode()

        self.at_creation()

    def write_sock(self, data):
        self.con.write(data.encode())


    def connect(self):
        if not self.connected:
            try:
                self.con = telnetlib.Telnet(self.host, self.port)
                self.out_thread.start()
                # self.con.sock.sendall(telnetlib.IAC + telnetlib.WILL + telnetlib.NAWS)
                self.con.sock.sendall(IAC + WILL + TTYPE)
                self.con.sock.sendall(IAC + SB + TTYPE + IS + self.clientname.encode() +  IAC +  SE)

                self.write_sock(self.loadstring)

                print( "%s connected successfuly" % self.botname)
                self.connected = True

            except socket.error:
                print( "%s unable to connect" % self.botname)

        elif self.connected:
            print( "You are already connected.")


    def disconnect(self):
        print( "Disconnecting %s..." % self.botname)

        self.out_thread._Thread__stop()

        time.sleep(1)

        self.con.close()
        self.connected = False

        for thread in self.tempthreads:
            thread._Thread__stop()



    def reconnect(self):
        print( "Reconnecting %s..." % self.username)

        time.sleep(1)

        self.out_thread._Thread__stop() 

        time.sleep(.001)

        self.con.close()
        self.connected = False

        self.con = telnetlib.Telnet(self.host, self.port)

        time.sleep(1)

        self.write_sock(self.loadstring)
        print( "%s connected successfuly" % self.botname)

        self.connected = True
        self.out_thread = threading.Thread(target=self.output)
        self.out_thread.start()


    def output(self, *args):
        while self.out_thread.isAlive():
            data = self.con.read_until('\n'.encode())

            data = self.format_ansi(data)

            if self.OUTPUT_ALL:
                if len(data) > 0:
                    print( data[:-1])

            self.run_triggers(data.strip())



    def do(self, action):
        action = '\n'.join(action.strip().split(";")) + '\n'

        self.write_sock(action)



    def doafter(self, delay, action):
        # self.delay = delay
        # self.action = action
        self.tempthreads.append(threading.Thread(target=self._doafter_func, args=(delay, action)))
        self.tempthreads[-1].start()


    def _doafter_func(self, *args):
        action = args[1]
        delay = args[0]
        time.sleep(delay)
        try:
            action()
        except:
            try:
                self.do(action)
            except:
                # raise 
                pass


    def weed_dead(self):
        for thread in self.tempthreads:
            if not thread.isAlive():
                self.tempthreads.remove(thread)


    def format_ansi(self, string):
        string = string.decode("utf-8")
        escape1 = re.compile(r'\x1b\[\d+m')
        escape2 = re.compile(r'\x1b\[\d+;\d+m')

        string = escape1.sub('', string)
        string = escape2.sub('', string)
        return string


    def run_triggers(self, string):
        self.weed_dead()
        for name in self.triggers:
            matches = re.match(self.triggers[name]['regex'], string)

            if matches:
                self.triggers[name]['code'](string, matches.groups(), self)

            elif not matches and self.triggers[name]['regex'] in string:
                self.triggers[name]['code'](string, (string), self)



    def add_trigger(self, regex, code, name):
        self.triggers[name] = {}
        self.triggers[name]['code'] = code
        self.triggers[name]['regex'] = regex



    def at_creation(self):
        pass


