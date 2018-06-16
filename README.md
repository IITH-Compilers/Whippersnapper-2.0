P4Benchmark
=============

Tool to benchmark P4 Compilers and Targets

Installation
------------

Run the following commands::

    pip install -r requirements.txt
    python setup.py install

Generate P4 Program and PCAP file for testing
---------------------------------------------

``'--version' option can be used to set the P4 Program language to 14/16``


* **Benchmark parse field**

The generated P4 program parses Ethernet,
PTP and a customized header containing 4 fields and each field is 16-bit wide::

    p4benchmark --feature parse-field --fields 4 

* **Benchmark parse header**

The generated P4 program parses Ethernet, PTP and
a customized number of headers each containing a customized number of fields.
Each field is 16-bit wide::

    p4benchmark --feature parse-header --fields 4 --headers 4

* **Benchmark parse complex**

The generated P4 program parses Ethernet, PTP and
a parse graph that has the depth of 2 and each node has 2 branches::

    p4benchmark --feature parse-complex --depth 2 --fanout 2

* **Benchmark action complexity**

The generated P4 program has N=2 number of set-field operations::

    p4benchmark --feature set-field --operations 2

* **Benchmark header addition**

The generated P4 program adds N=2 number of headers to packets::

    p4benchmark --feature add-header --headers 2

* **Benchmark header removal**

The generated P4 program removes N=2 number of headers to packets::

    p4benchmark --feature rm-header --headers 2

* **Benchmark processing pipeline**

The generated P4 program applies N=2 number of tables::

    p4benchmark --feature pipeline --tables 2 --table-size 32

* **Benchmark Read State**

The generated P4 program declares 1 register and performs 10 number of read operations::

    p4benchmark --feature read-state --registers 1 --operation 10

* **Benchmark Write State**

The generated P4 program declares 1 register and performs 10 number of write operations::

    p4benchmark --feature write-state --registers 1 --operation 10

Generated Files
---------------

The `output` directory contains::

    $ ls output
    commands.txt  main.p4  run_switch.sh  run_test.py  test.pcap

    1. main.p4        The desired program to benchmark a particular feature of the P4 target
    2. test.pcap      Sample packet crafted to match the parser or tables
    3. run_switch.sh  Script to run and configure bmv2
    4. commands.txt   Match-action rules for tables
    5. run_test.py    Python packet generator and receiver


Run Behavioral Target
---------------------
Require Behavioral Model 2 and P4C::

    $ cd output
    $ ./run_switch

Run Python packet generator
---------------------------

In another terminal, run::

    $ cd output
    $ sudo ./run_test.py --nb-headers 1 --nb-fields 4

PKTGEN (Send PCAP file)
-----------------------

Or, you could use a high performance packet generator that sends the prepared
PCAP file and sniffs for returning packets

**Build**

Requrire `cmake` and `libpcap`::

    cd pktgen
    mkdir build
    cd build
    cmake ..
    make

**Run pktgen**

This packet generator reads the prepared PCAP file and send `c` copies of that
packet at `t` Byte per second out of the interface `veth4`. The result is stored
in the `result` directory::

    $ p4benchmark/pktgen/build
    $ sudo ./p4benchmark -p ../../output/test.pcap -i veth4 -c 10000 -t 10000 -o result

TO MEASURE LATENCIES
--------------------

On compiling the p4 program, with the suitable compiler backend, a configuration file is produced. This configuration can be dumped onto the respective hardware component, say FPGA/PISCES. 
The output produced by Whippersnapper 2.0 is capable of running the p4 program on p4 software switch aka bmv2 or behaviour model version 2.
The test.pcap file has the structure of the packet to be sent.
To measure the latency produced by simple_switch (the time for packet to be processed and pass out of the switch) can be measured in two ways:

# Using pktgen: Build pktgen, by the above procedure

**Setup**
```
	sudo ./veth_setup.sh -- once per session
	g++ DataAlgo.cpp -o DataAlgo
	g++ Percent.cpp -o Percent
	Change lines 21, 61, 63 in measure_latency.sh according to the feature being tested.
```

**Run Test**
```	
sudo ./measure_latency.sh -- give desired no of packets, transmission rate and version, ex: 10000, 10000, 16
```

The latency values will be stored to <feature>-<version>-<packets>-<rate>.txt and the normalised percentage alues will be stored to <feature>-<version>-<packets>-<rate>-Percent.txt

DataAlgo filters the outliers in the dataset to some extent. It first calculates the mean of entire data, then clusters data surrounding the mean within an offset of standard deviation and then recalculates the mean of this clustered data. 

# Using tshark (3rd party)

**Setup**
```
	sudo apt install tshark
	cd /usr/share/wireshark/
	nano init.lua  -- In line 29 set disable_lua = true
	change line 27 of latency_new.sh according to the feature being tested.
```
**Run Test**
```
	sudo ./latency_new.sh -- give desired no of packets and version, ex: 10000, 16`
```

# Working
The above script is to automate the testing of a feature completely. The actual process going on is
1. The p4benchmark will produce the output directory to test certain feature.
2. The main.p4 program will be compiled with p4c-bm2-ss compiler.
3. tshark will monitor the interfaces being used by the switch, and to print timestamp to csv files.
4. A simple_switch will be setup with the main.json file and with some veth interfaces as its ports.
5. RuntimeCLI will populate the match-action tables of simple_switch from commands.txt.
6. The run_test.py file will send n copies of test.pcap file to simple_switch port.
7. The simple_switch will process the packet recieved on the ingress port and send the output packet to the egress port.
8. The packet arrival epoch timestamps and their number will be printed to a file on both ingress and egress interfaces.
9. Average of difference of these timestamps is taken for all the packets, which represents the latency.
10. An algorithm is used to eliminate buggy values due to glitches in packet transfer, droppings. This is based on the fact that latency values are expected to be similar for each packet. The latency values are divided into various category. The category having the highest frequency will be the one to be selected and average of all values of only that category will be calculated. Note that if two categories are having major frequency count which is a rare case, we don't get much error by considering only one of them.


