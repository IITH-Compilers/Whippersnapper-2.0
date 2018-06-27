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
# VERSION="16"
# PACKETS="10000"

ps -ef | grep simple_switch | grep -v grep | awk '{print $2}' | xargs kill
#ps -ef | grep tshark | grep -v grep | awk '{print $2}' | xargs kill

rm latency.csv
rm -rf output/

for((j=1;j<=3;j++));
do
        for ((i=1;i<=5;i++));
        do
                rm test_in.csv
                rm test_out.csv

		p4benchmark --feature pipeline --tables $i --table-size 32 --version $VERSION
		#p4benchmark --feature parse-complex --depth $i --fanout 2 --version $VERSION
		#p4benchmark --feature set-field --operations $i --version $VERSION
                #p4benchmark --feature parse-header --fields 2 --headers $i --version $VERSION
                cd output

                set -m
                $P4C_BM_SCRIPT --p4v $VERSION $PROG.p4 -o $PROG.json

                if [ $? -ne 0 ]; then
                echo "p4 compilation failed"
                exit 1
                fi
                sudo tshark -c $PACKETS -i veth0 -T fields -e frame.time_epoch -e frame.number -E header=n -E quote=d -E occurrence=f >> ../test_in.csv &
                sudo tshark -c $PACKETS -i veth4 -T fields -e frame.time_epoch -e frame.number -E header=n -E quote=d -E occurrence=f >> ../test_out.csv &
                sleep 6

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

                ./run_test.py -n $PACKETS

                ps -ef | grep simple_switch | grep -v grep | awk '{print $2}' | xargs kill

                echo "Killed Switch Process" 

                cd ..
                sleep 5
                python edit_csv.py >> latency.csv
                ps -ef | grep tshark | grep -v grep | awk '{print $2}' | xargs kill
        done
done

