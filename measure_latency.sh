#!/bin/bash

BMV2_PATH=../../behavioral-model
P4C_BM_PATH=../../p4c
PKTGEN_PATH=../pktgen/build/p4benchmark
P4C_BM_SCRIPT=p4c-bm2-ss
SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch
CLI_PATH=$BMV2_PATH/tools/runtime_CLI.py


PROG="main"

read -p "Enter the language version {14|16} = " VERSION
read -p "No. of Packets to send = " PACKETS
read -p "Rate of sending packets(bytes/sec) = " RATE
   
rm -rf output/

for i in 1 2 3
do
	p4benchmark --feature parse-header --headers $i --fields 2 --version $VERSION
	
	cd output
	
	set -m
	$P4C_BM_SCRIPT --std p4-$VERSION $PROG.p4 -o $PROG.json

	if [ $? -ne 0 ]; then
	echo "p4 compilation failed"
	exit 1
	fi

	sudo echo "sudo" > /dev/null
	sudo $SWITCH_PATH >/dev/null 2>&1
	sudo $SWITCH_PATH $PROG.json \
	    -i 0@veth0 -i 1@veth2 -i 2@veth4 -i 3@veth6 -i 4@veth8 \
	    --log-console &

	sleep 2
	echo "**************************************"
	echo "Sending commands to switch through CLI"
	echo "**************************************"
	$CLI_PATH --json $PROG.json < commands.txt 

	echo "READY!!!" 
	
	echo "Running the pktgen" 
	./$PKTGEN_PATH -p test.pcap -i veth4 -s veth0 -c $PACKETS -t $RATE 
	echo "Completed pktgen" 
	
    ps -ef | grep simple_switch | grep -v grep | awk '{print $2}' | xargs kill

	echo "Killed Switch Process" 
	
	cd ..

	./DataAlgo

done

cp output/data.txt header-$VERSION-$PACKETS-$RATE.txt

