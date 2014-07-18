#! /bin/bash
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

#-------------------------------------------------------------------------------
# send a periodic gratuitous ARP to insure that learning VXLAN service
# nodes are kept up to date
#

if [ $# != 0 ]
then
    echo ""
    echo "usage: vxrd"
    echo ""
    echo "VXlan Refresh Daemon sends a gratuitous ARP (using arping) to the subnet"
    echo "broadcast address for each vtep to insure that a learning service node is"
    echo "kept up to date.  ARPs are sent every 30 seconds."
    echo ""
    exit 1
fi

[ $UID == 0 ] || { echo "must be root" && exit 1; }

while /bin/true
do
    vteps=$(ip -d -oneline link show | grep vxlan | awk '{print $2}' | sed -e "s/://")

    for V in $vteps
    do
    # target/from the subnet broadcast... nobody will respond
        arping -q -c 1 -b -B -i $V &> /dev/null
    done
    sleep 30
done

