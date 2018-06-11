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

for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30
do
	p4benchmark --feature pipeline --tables $i --table-size 32 --version $VERSION
	
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

./Percent pipeline-$VERSION-$PACKETS-$RATE-Percent.txt

cp output/data.txt pipeline-$VERSION-$PACKETS-$RATE.txt

