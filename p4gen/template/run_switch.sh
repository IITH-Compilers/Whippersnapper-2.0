
BMV2_PATH=../../behavioral-model
P4C_BM_PATH=../../p4c
P4C_BM_SCRIPT=p4c-bm2-ss


PROG="main"

read -p "Enter the language version {p4-14|p4-16} = " VERSION

set -m
$P4C_BM_SCRIPT --std $VERSION $PROG.p4 -o $PROG.json

if [ $? -ne 0 ]; then
echo "p4 compilation failed"
exit 1
fi

SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch

CLI_PATH=$BMV2_PATH/tools/runtime_CLI.py

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
fg
