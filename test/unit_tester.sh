#!/bin/bash
chmod +x ./test/script/*

test_tcp()
{
	make server >/dev/null
	sleep 1
	echo status | make client &
	echo status | make client    >/dev/null
}

run_test()
{
	echo "new test"
	echo "============================="
	make server FILE=$2 >/dev/null
	sleep 1
	OUTPUT=`($1) | ./client/client.py`
	echo $OUTPUT
	echo exit  | ./client/client.py >/dev/null
}

# test_tcp
#status
run_test "echo status"

#start, stop, restart
run_test "./test/script/start_stop_restart.sh"

##stoptime
# run_test  "./test/script/stoptime.sh"

##exit
run_test "echo exit"

##startretries

#echo ""
