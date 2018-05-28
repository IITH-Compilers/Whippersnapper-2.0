#!/usr/bin/env python

import os
from subprocess import call, Popen, PIPE
import shlex
import time
import argparse

dir_path = os.path.dirname(os.path.realpath(__file__))

class P4vSwitch(object):
    def __init__(self, p4_program='', rules=''):
        self.ovs = os.environ.get('OVS_PATH')
        self.dpdk = os.environ.get('DPDK_BUILD')
        self.p4_program = p4_program
        self.rules = rules

    def configure(self):
        cmd  = "{0}/configure --with-dpdk={1} ".format(self.ovs, self.dpdk)
        cmd += "CFLAGS=\"-g -O2 -Wno-cast-align\" "
        cmd += "p4inputfile={0} ".format(self.p4_program)
        cmd += "p4outputdir=./include/p4/src"
        print cmd
        p = Popen(shlex.split(cmd))
        p.wait()
        assert (p.returncode == 0)

    def make_switch(self):
        cmd = "make -j4"
        print cmd
        p = Popen(shlex.split(cmd))
        p.wait()
        assert (p.returncode == 0)

    def start_ovsdb_server(self):
        cmd  = "sudo ./ovsdb/ovsdb-server "
        cmd += "--remote=punix:/usr/local/var/run/openvswitch/db.sock "
        cmd += "--remote=db:Open_vSwitch,Open_vSwitch,manager_options --pidfile"
        print cmd
        return Popen(shlex.split(cmd))

    def start_ovs_vswitchd(self):
        cmd  = "sudo ./vswitchd/ovs-vswitchd --dpdk -c 0x1 -n 4 -- "
        cmd += "unix:/usr/local/var/run/openvswitch/db.sock --pidfile"
        print cmd
        return Popen(shlex.split(cmd))

    def add_flows(self, command_file):
        with open(command_file, 'r') as fin:
            for line in fin:
                cmd = """sudo {0}/{1}""".format('utilities', line)
                print cmd
                p = Popen(shlex.split(cmd))
                p.wait()

    def stop_ovs_vswitchd(self):
        cmd = 'sudo pkill ovs-vswitchd'
    	args = shlex.split(cmd)
    	p = Popen(args)
    	p.wait()

    def stop_ovsdb_server(self):
        cmd = 'sudo pkill ovsdb-server'
    	args = shlex.split(cmd)
    	p = Popen(args)
    	p.wait()

    def compile(self):
        if (os.path.isfile(self.p4_program)):
            self.clean()
            self.configure()
            self.make_switch()
        else:
            print "'%s' is not a valid file" % self.p4_program

    def run(self):
        ovsdb = self.start_ovsdb_server()
        vswitchd = self.start_ovs_vswitchd()
        time.sleep(1)
        self.add_flows(os.path.join(dir_path, 'vs_commands.txt'))
        if (os.path.isfile(self.rules)):
		self.add_flows(self.rules)
        else:
            print "Rules are not added"
        vswitchd.wait()
	ovsdb.wait()

    def stop_all(self):
        self.stop_ovs_vswitchd()
        self.stop_ovsdb_server()

    def clean(self):
        cmd = 'make clean'
        p = Popen(shlex.split(cmd))
        p.wait()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='P4 Benchmark')
    parser.add_argument('-k', '--kill-ovs', default=False, action='store_true',
                        help='kill ovsdb server and vswitchd')
    parser.add_argument('-c', '--compile', default=False, action='store_true',
                        help='compile the P4 program for Pisces')
    parser.add_argument('-p', '--p4-program', default='', type=str,
                        help='path to the P4 program')
    parser.add_argument('-r', '--rules', default='commands.txt',
                        help='Rules for the program')
    args = parser.parse_args()

    print args.p4_program
    pisces = P4vSwitch(args.p4_program, args.rules)

    if args.kill_ovs:
        pisces.stop_all()
    elif args.compile:
        pisces.compile()
    else:
        pisces.run()
