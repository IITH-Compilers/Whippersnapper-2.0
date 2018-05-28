#!/usr/bin/env python

import os
from subprocess import call, Popen, PIPE
import shlex
import time
import argparse

class P4Benchmark(object):
    def __init__(self, parent_dir, directory, offer_load):
        assert os.environ.get('P4BENCHMARK_ROOT')
        assert os.environ.get('PYTHONPATH')
        pypath = os.environ.get('PYTHONPATH')
        p4bench = os.environ.get('P4BENCHMARK_ROOT')
        bmv2 = os.path.join(p4bench, 'behavioral-model')
        self.p4c = os.path.join(p4bench, 'p4c-bm/p4c_bm/__main__.py')
        self.switch_path = os.path.join(bmv2, 'targets/simple_switch/simple_switch')
        self.cli_path = os.path.join(bmv2, 'tools/runtime_CLI.py')
        self.pktgen = os.path.join(p4bench, 'pktgen/build/p4benchmark')
        self.sendb2b = os.path.join(p4bench, 'pktgen/build/sendb2b')
        self.analyse = os.path.join(p4bench, 'benchmark/analyse.R')
        self.nb_packets = 100000
        self.log_level = ''
        self.parent_dir = parent_dir
        self.directory = directory
        self.offer_load = offer_load

    def add_rules(self, json_path, commands, retries):
        if retries > 0:
            cmd = [self.cli_path, '--json', json_path]
            if os.path.isfile(commands):
                with open(commands, "r") as f:
                    p = Popen(cmd, stdin=f, stdout=PIPE, stderr=PIPE)
                    out, err = p.communicate()
                    if out:
                        print out
                        if "Could not" in out:
                            print "Retry in 1 second"
                            time.sleep(1)
                            return self.add_rules(json_path, port_number, commands, retries-1)
                        elif  "DUPLICATE_ENTRY" in out:
                            pass
                    if err:
                        print err
                        time.sleep(1)
                        return self.add_rules(json_path, port_number, commands, retries-1)

    def has_lost_packet(self):
        with open('%s/loss.csv' % self.directory, 'r') as f:
            for line in f:
                pass
            data = shlex.split(line)
            assert (len(data) == 3)
            sent = float(data[0])
            recv = float(data[1])
        return (recv < sent)


    def run_analyser(self):
        cmd = '{0} {1}'.format(self.analyse, self.parent_dir)
        print cmd
        args = shlex.split(cmd)
        p = Popen(args)
        p.wait()

    def tearDown(self):
        cmd = 'sudo pkill lt-simple_swi'
        args = shlex.split(cmd)
        p = Popen(args)
        out, err = p.communicate()
        if out:
            print out
        if err:
            print err
        self.p.wait()
        assert (self.p.poll() != None)
        time.sleep(5)

    def start(self):
        # run switch
        self.run_behavioral_switch()
        # run packet generator
        self.run_packet_generator()
        # stop the switch
        self.tearDown()

    def run_behavioral_switch(self):
        prog = 'main'
        json_path = 'output/%s.json' % prog
        commands = 'output/commands.txt'
        cmd = 'sudo {0} {1} -i0@veth0 -i1@veth2 -i 2@veth4 {2}'.format(self.switch_path,
                json_path, self.log_level)
        print cmd
        args = shlex.split(cmd)
        out_file = '{0}/bmv2.log'.format(self.directory)
        with open(out_file, 'w') as out:
            out.write('Number of packets: %d\n' % self.nb_packets)
            out.write('Offered load:  %d\n' % self.offer_load)
            self.p = Popen(args, stdout=out, stderr=out, shell=False)
        assert (self.p.poll() == None)
        # wait for the switch to start
        time.sleep(2)
        # insert rules: retry 3 times if not succeed
        self.add_rules(json_path, commands, 3)

    def run_packet_generator(self):
        cmd = 'sudo {0} -p {1} -i veth4 -c {2} -t {3}'.format(self.pktgen,
            'output/test.pcap', self.nb_packets, self.offer_load)
        print cmd
        args = shlex.split(cmd)
        out_file = '{0}/latency.csv'.format(self.directory)
        err_file = '{0}/loss.csv'.format(self.directory)
        out = open(out_file, 'w+')
        err = open(err_file, 'w+')
        p = Popen(args, stdout=out, stderr=err)
        p.wait()
        out.close()
        err.close()

    def measure_latency(self):
        cmd = 'sudo {0} -p {1} -s veth2 -i veth4 -c {2} '.format(
            self.sendb2b,
            'output/test.pcap',
            self.nb_packets)
        print cmd
        args = shlex.split(cmd)
        out_file = '{0}/latency.csv'.format(self.directory)
        err_file = '{0}/loss.csv'.format(self.directory)
        out = open(out_file, 'w+')
        err = open(err_file, 'w+')
        p = Popen(args, stdout=out, stderr=err)
        p.wait()
        out.close()
        err.close()

