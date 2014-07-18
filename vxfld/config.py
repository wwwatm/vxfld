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

"""
Configuration object

Typical usage:
    Create object (config = Config()
    load in checker functions
    load with defaults
    load with cmd line options from argparse, if desired
"""

import socket


class Config:
    """ Generic Config class. """

    def __init__(self):
        self._checkers = {}

    def set_param(self, name, value):
        """
        If there is a checker function for this parameter, call it
        with value.  Otherwise simply set an attribute with the name
        to the value.
        """

        if name in self._checkers:
            # Let checker do it's thing before setting
            result = self._checkers[name][0](self, value)
            setattr(self, name, result)

            # Now call cb function.
            if self._checkers[name][1]:
                self._checkers[name][1](self)
        else:
            # No checker, just set val
            setattr(self, name, value)

    def del_param(self, name):
        """ Delete the parameter altogether.

        Useful for clearing out a parameter where the set is additive.
        """
        pass

    def read_file(self, fn):
        """ Read config from file fn and process each line. """

        COMMENT_CHAR = '#'
        OPTION_CHAR = '='
        try:
            fd = open(fn)
        except Exception as e:
            raise RuntimeError('Cannot open config file %s: %s' % (fn, str(e)))
        with fd:
            for line in fd:
                # First, remove comments:
                if COMMENT_CHAR in line:
                    line, comment = line.split(COMMENT_CHAR, 1)
                # Second, find lines with an option=value:
                if OPTION_CHAR in line:
                    option, value = line.split(OPTION_CHAR, 1)
                    option = option.strip()
                    value = value.strip()
                    if hasattr(self, option):
                        self.set_param(option.strip(), value.strip())
                    else:
                        msg = 'Unknown variable "%s" in config file %s' % \
                              (option, fn)
                        raise RuntimeError(msg)

    def checker(self, func, param=None, callback=None):
        """
        Set the function as the checker function for the named
        parameter.  If no parameter name given, use the function name.
        """

        if not param:
            param = func.__name__
        self._checkers[param] = (func, callback)

    # Common checker functions
    def int_checker(self, param, cb=None):
        self._checkers[param] = (Config._int_checker, cb)

    def _int_checker(self, val):
        """ Returns int from string or int. """
        try:
            return int(val)
        except:
            raise RuntimeError('Invalid integer value %s' % val)

    def bool_checker(self, param, cb=None):
        self._checkers[param] = (Config._bool_checker, cb)

    def _bool_checker(self, val):
        """ Returns True for string true or boolean True. """

        if type(val) is bool:
            return val
        val = val.lower()
        if val == 'true':
            return True
        return False

    def list_checker(self, param, cb=None):
        self._checkers[param] = (Config._list_checker, cb)

    def _list_checker(self, val):
        """ Returns a list by splitting string. """
        try:
            return val.split()
        except:
            raise RuntimeError('Invalid string for list value %s' % val)

    def addr_checker(self, param, cb=None):
        self._checkers[param] = (Config._addr_checker, cb)

    def _addr_checker(self, s):
        """ Returns the result of gethostbyname on a string.

        verifies correctness of a dotted decimal specificationi.
        """

        try:
            return socket.gethostbyname(s)
        except:
            raise RuntimeError('Invalid address %s' % s)


defaults = {
    # A dictionary to prime the config object with all config attrs plus
    # some constants.
    #
    # This dict sets up all the default values.  It also primes the
    # config obj with all the attrs needed so we don't have to test
    # for existence every time a param is accessed.  Also, loading
    # from a config file requires the config variables to be
    # pre-loaded since a non-existent attribute is taken to be a
    # config file error.

    # Common to both snd and rd
    'protocol_version': '0.1',  # a constant
    'loglevel': 'INFO',
    'logdest': 'syslog',
    'monitor': 'false',  # set to true to monitor with monit
    'pidfile': '/var/run/vxfld.pid',
    'vxlan_port': '4789',  # port for vxlan tunnel pkts
    'vxfld_port': '10001',  # port for vxfld messages
    'holdtime': '90',  # how long to hold soft state

    #  vxsnd specific.  Add these here to prime the config object with
    #  these attributes before config file is read.  Does no harm if
    #  included by vxrd
    'address': '',
    'install_addr': 'false',
    'servers': '',
    'age_check': '90',  # frequency to age out stale fdb entries
    'vtep_membership': '',  # not yet implemented

    #  .. and vxrd specific.
    'local_addr': '',  # Used if none configured on vxlan if
    'svcnode': '',  # Used if none configured on vxlan if
    'refresh_rate': '3',  # how often to refresh within holdtime
    'config_check_rate': 30  # secs between checking for config changes
}


def loglevel(c, val):
    """
    Checker functions for attrs which go beyond the basic int, list, bool.
    """

    import logging

    lvl = getattr(logging, val.upper(), None)
    if not lvl:
        raise RuntimeError('Invalid log level %s' % val)
    logging.getLogger('vxfld').setLevel(lvl)
    return lvl


def servers(c, val):
    # split the string and resolve to set of addresses.
    result = set()
    l = val.split()
    for s in l:
        try:
            a = socket.gethostbyname(s)
        except:
            lgr.warning('Cannot resolve address for server %s' % s)
            continue
        result |= set([a])
    return result


def init(args):
    """ Called to setup initial Config object. """
    config = Config()

    # set up checker funtions first

    # common
    config.checker(loglevel)
    config.bool_checker('monitor')
    config.int_checker('vxlan_port')
    config.int_checker('vxfld_port')
    config.int_checker('holdtime')

    # vxsnd
    config.addr_checker('address')
    config.bool_checker('install_addr')
    config.checker(servers)
    config.int_checker('age_check')

    # vxrd
    config.addr_checker('local_addr')
    config.addr_checker('svcnode')
    config.int_checker('refresh_rate')
    config.int_checker('config_check_rate')

    # Load the defaults
    for (p, v) in defaults.items():
        config.set_param(p, v)

    # Over-write with settings from config file
    #  args must contain this attr
    config.read_file(args.config_file)

    for (p, v) in vars(args).items():
        if v is not None:
            config.set_param(p, v)

    return config


if __name__ == '__main__':
    # This main is currently broken
    #

    import logging

    config = init()

    lgr = logging.getLogger('vxfld')
    print 'Default log level: ', lgr.getEffectiveLevel()
    config.set_param('loglevel', 'DEBUG')
    print 'Changed log level: ', lgr.getEffectiveLevel()

    print 'Default vxlan port:', config.vxlan_port
    config.set_param('vxlan_port', '8081')
    print 'Changed vxlan port:', config.vxlan_port
    print vars(config)
