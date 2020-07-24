#!/bin/bash

chmod +x ./test/script/*
MAKEFLAGS="--no-print-directory -s"

test_yml()
{
	for file in ./test/yaml/*
	do
		echo "Testing [$(basename "${file}")]"
		echo "============================="
		echo ""
		make server FILE=$file
		echo ""
		echo exit | ./client/client.py >/dev/null
		sleep 1
	done
}

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
	echo ""
	make server FILE=$2 >/dev/null
	sleep 1
	OUTPUT=`($1) | ./client/client.py`
	echo $OUTPUT
	echo exit  | ./client/client.py >/dev/null
	echo ""
}

test_yml
# test_tcp
#status
run_test "echo status"

#start, stop, restart
run_test "./test/script/start_stop_restart.sh" "./test/yaml/start_stop_restart.yml"

##stoptime
# run_test  "./test/script/stoptime.sh"

##exit
run_test "echo exit"

#startretries
run_test "" "./test/yaml/startretries.yml"

#signal
gcc ./test/script/signal_program.c -o ./test/script/signal
run_test "echo stop signal"  "./test/yaml/signal.yml"
