#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Cumulus Networks, Inc. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc.
# 51 Franklin Street, Fifth Floor
# Boston, MA  02110-1301, USA.

"""
Client and Server for Management

A utility uses the client class to send a message to the daemon
with a request.  The daemon runs the server object in a thread and
responds to these requests.  The response is two objects: the valid
response if no error and an exception object if there is an error.
One of the two should be None.

See the test code for typical usage.
"""


import socket
import pickle
import select
import struct
import os
import threading

import pdb


class MgmtServer(socket.socket):

    def __init__(self, uds_file):

        self.clients = {}

        try:
            os.unlink(uds_file)
        except OSError:
            if os.path.exists(uds_file):
                raise

        socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.bind(uds_file)
        except Exception as e:
            raise RuntimeError('Unable to bind to mgmt socket %s: %s'
                               % (uds_file, str(e)))
        self.listen(5)
        self.epoll = select.epoll()
        self.epoll.register(self.fileno(), select.EPOLLIN)

    def client_close(self, fileno):

        self.epoll.unregister(fileno)
        self.clients[fileno].close()
        del self.clients[fileno]

    def run(self):

        while True:

            events = self.epoll.poll()
            for fileno, event in events:
                if fileno == self.fileno():
                    client, address = self.accept()
                    self.epoll.register(client.fileno(), select.EPOLLIN)
                    self.clients[client.fileno()] = client

                elif event & select.EPOLLIN:
                    client = self.clients[fileno]
                    try:
                        buf = client.recv(4096)
                        if not buf:   # EOF
                            self.client_close(fileno)
                            continue
                    except socket.error as e:
                        self.client_close(fileno)

                    msg = pickle.loads(buf)
                    out, err = self.process(msg)
                    output = pickle.dumps((out, err), pickle.HIGHEST_PROTOCOL)

                    try:
                        client.sendall(struct.pack('I', len(output)))
                        client.sendall(output)
                    except socket.error as e:
                        self.client_close(fileno)

    def process(self, msg):
        # Returns a response object and an Exception object.  The
        # latter is None if no exception

        # Over-ride this method in the derived class
        print 'Base class:', msg
        return None, None

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.setDaemon(True)
        thread.start()


class MgmtClient(socket.socket):

    def __init__(self, uds_file):
        try:
            socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)
            self.connect(uds_file)

        except socket.error, (errno, string):
            msg = "Unable to connect to daemon on socket %s [%d]: %s" % \
                  (uds_file, errno, string)
            raise RuntimeError(msg)

    def sendobj(self, msgobj):
        msg = pickle.dumps(msgobj, pickle.HIGHEST_PROTOCOL)

        self.sendall(msg)

        size = int(struct.unpack('I', self.recv(4))[0])
        read_bytes = 0
        resp = ""

        while read_bytes < size:
            resp += self.recv(2048)
            read_bytes = len(resp)

        out, err = pickle.loads(resp)
        return out, err


if __name__ == '__main__':
    from docopt import docopt

    usage = '''
Usage:
    mgmtserver -h
    mgmtserver -f UDS_FILE (-s | -c )

Options:
    -f UDS_FILE  : File name for Unix domain socket
    -s           : Run in server mode
    -c           : Run in client mode

This will test the Mgmtserver by instantiating a echo server or client
'''

    class EchoMgmtServer(MgmtServer):
        def process(self, msg):
            print 'Received msg:', msg
            return 'Thanks for the msg of len %d' % len(msg), None

    args = docopt(usage)

    if args['-s']:
        try:
            s = EchoMgmtServer(args['-f'])
            s.run()
        except KeyboardInterrupt:
            exit()

    if args['-c']:
        c = MgmtClient(args['-f'])
        for msg in ('Here is first message',
                    'Here is second',
                    'And third',
                    ):
            print 'Sending "%s"' % msg
            resp = c.sendobj(msg)
            print 'Response: "%s"' % resp

        msg = {'key1': 1, 'key2': 2, 'key3': 3}
        print 'Sending "%s"' % msg
        resp, err = c.sendobj(msg)
        if err:
            print 'Received error %s' % str(err)
        print 'Response: "%s"' % resp
