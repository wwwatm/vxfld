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

""" Stuff that is common to both vxfld daemons. """
import os
import sys
import signal
import subprocess
import atexit
import argparse
import logging
import logging.handlers
import vxfld.config


def run_cmd(cmd, verbose=False):
    """
    Runs a command with Popen gathering output & status. Takes a str arg.
    Should take a list too
    """

    cmd_list = cmd.split()
    try:
        proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=False)
        stdout, stderr = proc.communicate()
        proc.wait()
    except Exception as e:
        raise RuntimeError('Failed to run shell cmd %s: %s' % (cmd, str(e)))
    return (stdout, stderr, proc.returncode)


def logger_setup(conf):
    """ Setup logging. """
    global lgr
    lgr = logging.getLogger('vxfld')

    p = os.path.basename(sys.argv[0])
    lgr_fmt = '%%(asctime)s %s %%(levelname)s: %%(message)s' % p

    if conf.logdest == 'syslog':
        h = logging.handlers.SysLogHandler(address='/dev/log')
        syslog_fmt = '%s: %%(levelname)s: %%(message)s' % p
        f = logging.Formatter(fmt=syslog_fmt)
        h.setFormatter(f)
        lgr.addHandler(h)
        lgr.setLevel(conf.loglevel)
        return lgr
    if conf.logdest == 'stdout':
        logging.basicConfig(level=conf.loglevel,
                            format=lgr_fmt,
                            datefmt='%H:%M:%S')
        return lgr

    # logdest is a file
    logging.basicConfig(filename=conf.logdest,
                        level=conf.loglevel,
                        format=lgr_fmt,
                        datefmt='%H:%M:%S')
    return lgr


def write_pidfile(pf):
    """ check/create/delete pidfile to avoid duplicate instances

    pidfile is a global since we have to register it's delete-on-exit handler
    pid fd is global. Otherwise OS reclaims lock if fd closed
    """

    import fcntl

    global pidfile
    global pidfd
    pidfile = os.path.abspath(pf)

    pid = str(os.getpid())
    try:
        # Mode is append so we don't truncate until we get lock
        f = open(pidfile, 'a')
    except:
        raise RuntimeError("Cannot open pid file %s" % pidfile)
    lgr.debug("Opened pid file %s" % pidfile)
    try:
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        raise RuntimeError("Unable to lock pid file")

    # Now we can register the callback to del the file on exit and
    # write the pid into the file
    atexit.register(delpid)
    f.truncate(0)
    f.write("{0}\n".format(pid))
    f.flush()
    pidfd = f

    # we're good to go
    #
    return pid


def delpid():
    try:
        os.remove(pidfile)
    except Exception as e:
        lgr.critical("Unable to remove pid file on exit: %s" % str(e))


def start_monit(service):
    # On failure just log.  Don't pass exception up
    try:
        (out, err, errno) = run_cmd('monit monitor %s 2>/dev/null' % service)
        if errno:
            raise RuntimeError('monit error %d', errno)
    except:
        lgr.warning('Failed to initialize monitoring with monit')


def term_handler(signum, frame):
    sys.exit(0)


def common_parser():
    """ Argparser for common cmd line args. """

    prsr = argparse.ArgumentParser()
    prsr.add_argument('-c', '--config-file',
                      default='/etc/vxfld.conf',
                      help='The config file to read in at startup')
    prsr.add_argument('-d', '--daemon',
                      action='store_true',
                      help='Run as a daemon program')
    prsr.add_argument('-p', '--pidfile',
                      help='File to write the process ID')
    prsr.add_argument('-u', '--udsfile', \
		      help='Unix domain socket for mgmt interface')
    prsr.add_argument('-l', '--logdest',
                      help='The destination for log records.  May be '
                           '"stdout", "syslog" or a file name')
    prsr.add_argument('-L', '--loglevel',
                      help='The severity level for which log records are '
                           'written to the log.  Allowed values in porder of '
                           'severity are: debug, info, warning, error, '
                           'critical')

    return prsr


def initial_setup(args):
    """ All the initial setup common to both daemons. """

    # Init config
    try:
        conf = vxfld.config.init(args)
    except Exception as e:
        # On error expecting a RuntimeError with nice msg
        sys.stderr.write('%s\n' % str(e))
        sys.exit(1)

    # Set up signal handlers before daemonizing
    signal.signal(signal.SIGINT, term_handler)
    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGHUP, term_handler)

    if conf.daemon:
        import daemon

        dc = daemon.DaemonContext(working_directory='/var/run')
        dc.open()

    # set up logging.  Must be after daemonizing.
    try:
        lgr = logger_setup(conf)
    except Exception as e:
        # If daemonized, stderr is /dev/null!
        sys.stderr.write('Unable to set up logging: %s\n' % str(e))
        sys.exit(1)

    # Announce my existence
    lgr.info("Starting (pid %d) ..." % os.getpid())
    atexit.register(lgr.info, "Terminating (pid %d)" % os.getpid())

    # Make sure that I am not already running
    try:
        write_pidfile(conf.pidfile)
    except RuntimeError as e:
        lgr.critical(str(e))
        sys.exit(1)

    return conf, lgr
