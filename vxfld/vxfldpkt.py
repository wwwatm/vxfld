#! /usr/bin/python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Cumulus Networks, Inc. All rights reserved.
# Copyright (C) 2014 Metacloud Inc.
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

import dpkt
import struct
import socket

# Message types

version = 1  # Protocol version


class MsgType():
    unknown = 0  # Never used
    refresh = 1
    resend = 2


class PktError(Exception):
    def __init__(self, msg):
        self.msg = msg


class Refresh(dpkt.Packet):
    """Packet sent between vxsnd entities to refresh the vvtuples."""

    __hdr__ = (
        ('version', 'B', 0x01),  # version of the protocol Packet
        ('type', 'B', MsgType.refresh),
        ('originator', 'H', 0),  # should be all flags
        ('holdtime', 'H', 0)
    )

    def __init__(self, *args, **kwargs):
        dpkt.Packet.__init__(self, **kwargs)
        self.vni_vteps = dict()
        if args:
            self.unpack(args[0])

    def unpack(self, buf):
        dpkt.Packet.unpack(self, buf)
        if self.version != version:
            raise PktError("Wrong version")
        data = self.data
        pos = 0
        data_len = len(data)
        while pos < data_len:
            (vni, cnt) = struct.unpack('>IH', data[pos:pos + 6])
            pos += 6
            if pos + cnt * 4 > data_len:
                raise PktError("Short packet")
            if not self.vni_vteps.get(vni, None):
                self.vni_vteps[vni] = []
            while cnt:
                ip = data[pos:pos + 4]
                self.vni_vteps[vni].append(socket.inet_ntoa(ip))
                cnt -= 1
                pos += 4

    def __str__(self):
        s = ''
        for (vni, iplist) in self.vni_vteps.items():
            s += struct.pack('>IH', vni, len(iplist))
            for ip in iplist:
                s += socket.inet_aton(ip)
        return self.pack_hdr() + s

    def __len__(self):
        cnt = 0
        for (vni, iplist) in self.vni_vteps.items():
            cnt += 4 + 2 + 4 * len(iplist)
        return self.__hdr_len__ + cnt

    def add_vni_vteps(self, vp):
        '''Add a set of <vni vtep_list>.'''

        for (vni, l) in vp.items():
            iplist = self.vni_vteps.get(vni, None)
            if iplist:
                iplist.extend(l)
            else:
                self.vni_vteps[vni] = l
