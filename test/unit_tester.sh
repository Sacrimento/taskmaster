#!/bin/bash

test_tcp()
{
	make server >/dev/null
	sleep 1
	echo status | make client &
	echo status | make client    >/dev/null
}

run_test()
{
	make server FILE=$2 >/dev/null
	sleep 1
	OUTPUT=`$1 | ./client/client.py`
	$1
	echo $OUTPUT
	echo exit  | ./client/client.py >/dev/null
}

# test_tcp
#status
run_test "echo status"

#start, stop, restart
text="start\nstop\nrestart\n"
run_test "printf $text"

##stoptime
text="stop stoptime\nstatus"
run_test "printf $text; sleep 30; printf 'status'"

##exit
# run_test "exit"

##startretries

#echo ""
