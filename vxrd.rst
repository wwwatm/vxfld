=====
vxrd
=====

-----------------------------------------
Registration daemon for VXLAN deployments
-----------------------------------------

:Manual section: 8


SYNOPSIS
========
vxrd [OPTIONS]


DESCRIPTION
===========

To receive flood packets from a Replicating service node, a VTEP must
register the VXLANs it belongs to.  ``vxrd`` is a process to
periodically register with the service node ``vxsnd(8)`` to keep the
VTEP endpoint membership active at the service node.

OPTIONS
=======

-c, \--config FILE
  The config file to load.  Default is /etc/vxrd.conf

-d, --daemon
  Run as a daemon program

-p, --pidfile FILE
  The filename for the PID file.  Default is /var/run/vxrd.pid

-l, \--logdest DEST
  The log destination.  One of ``stdout``, ``syslog`` or a file name.
  Default is ``syslog``.

-L, \--loglevel LEVEL
  The log level.  One of debug, info, warning, error, critical.
  Default is info

-s, --svcnode

  The address of the service node to send registration messages to.
  It is used for those VXLANs that do not have a svcnode explicitly
  specified on the vxlan interface.

-a, --local-addr

  The local tunnel endpoint address for all VXLAN
  interfaces which do not have an address explicitly
  specified.


Configuration
=============

All the options above and additional configuration options can be
speficied in a configuration file, read at startup.  All the
configuration options and their defaults are specified in the default
config file */etc/vxrd.conf*.  Options specified on the command line
take precedence over options specified in the config file.



SEE ALSO
========
``ip-link``\(8), ``brctl``\(8), ``vxsnd``\(8)

http://tools.ietf.org/id/draft-mahalingam-dutt-dcops-vxlan-00.txt


TODO
====

Listen to netlink events and send notifications immediately on link up/down


