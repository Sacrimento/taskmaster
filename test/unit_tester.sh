#!/bin/bash

chmod +x ./test/script/*
mkdir -p ./test/output
mkdir -p ./test/log
export MAKEFLAGS="--no-print-directory -s"

test_yml()
{
	for file in ./test/yaml/*
	do
		BASENAME=$(basename "${file}")
		log=./test/output/${BASENAME%.yml}.log
		echo "Testing [${BASENAME}]"
		echo "============================="
		make server FILE=$file OUTPUT=${log} > ./test/log/${BASENAME%.yml}.log
		echo exit | ./client/client.py >/dev/null
		# echo "=============================" >> $log
		# cat /tmp/log >> $log
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


##exit
run_test "echo exit"

#signal
gcc ./test/script/signal_program.c -o ./test/script/signal
run_test "echo stop signal"  "./test/yaml/signal.yml"

#stop time
gcc ./test/script/stoptime.c -o ./test/script/stoptime
run_test  "./test/script/stoptime.sh" "./test/yaml/stoptime.yml"

