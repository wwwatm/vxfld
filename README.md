# VXFLD

## VXLAN BUM Flooding Suite

VXFLD is a suite of tools that provides the ability to do VXLAN
BUM flooding using unicast instead of the traditional multicast.

This is accomplished using 2 components, [vxsnd](https://github.com/CumulusNetworks/vxfld/blob/master/vxsnd.rst)
and [vxrd](https://github.com/CumulusNetworks/vxfld/blob/master/vxrd.rst).

vxsnd provides the unicast BUM packet flooding and VTEP learing
capabilities while vxrd is a simple registration daemon designed to
register local VTEPs with a remote vxsnd daemon.

## TODO
- Requesting complete VNI dump from other node (initial startup)
- concurrency model
  - coroutines, eventlet/greenlet/greenthreads
  - 3 basic core functions today should have distince concurrency
    - BUM packet flooding
    - VNI registration
    - Replication
      - Sending VNI data to other node
      - Responding to VNI dump request from peer
- Unit tests
- pep8
- ability to run as non-priveleged user
- tiered replication/flooding
