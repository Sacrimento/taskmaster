#!/bin/bash

chmod +x ./test/script/*
mkdir -p ./test/output
mkdir -p ./test/log
rm -f ./test/output/*
rm -f ./test/log/*
export MAKEFLAGS="--no-print-directory -s"
trap "exit 1" TERM
export TOP_PID=$$
export DEFAULT_PORT=4242

RED="\e[91m"
GREEN="\e[92m"
DEFAULT="\e[39m"

test_print()
{
	if [ $1 -eq 0 ] ; then text="${GREEN}[OK]"; else text="${RED}[KO]"; fi
	echo -e "$2: ${text}${DEFAULT}"
}

test_yml()
{
	file="./test/yaml/$1"
	BASENAME=$1
	server_log="./test/output/${BASENAME%.yml}.log"
	log="./test/log/${BASENAME%.yml}.log"
	echo "Testing [${BASENAME}]"
	echo "============================="
	export DEFAULT_PORT=$((DEFAULT_PORT+1))
	export cmd="make server PORT=$DEFAULT_PORT FILE=$file OUTPUT=${server_log}"
	if [ -z "$VERBOSE" ]; then ($cmd > ${log});	else ($cmd); fi
	# test_print $? ${BASENAME}
	sleep 1
	echo exit | ./client/client.py -p $DEFAULT_PORT >/dev/null
}

exit_all_yml()
{
	sleep 12
	for file in ./test/yaml/*
	do
		echo $tmp
		tmp=$((tmp+1))
		echo exit | ./client/client.py -p $tmp >/dev/null
	done
}

function test_all_yml()
{
	tmp=4242
	if [ -z "$TEST" ]
	then	
		for file in ./test/yaml/*
		do
			test_yml $(basename "${file}")
		done
		sleep 1
	else
		test_yml "${TEST}.yml"
		exit
	fi
}

test_tcp()
{
	make server >/dev/null
	echo status | make client &
	echo status | make client    >/dev/null
}

run_test_2()
{
	echo "Testing [${2}]"
	echo "============================="
	server_log=./test/output/manual_test_$2.log
	log=./test/log/manual_test_$2.log
	export DEFAULT_PORT=$((DEFAULT_PORT+1))

	export cmd="make server PORT=$DEFAULT_PORT FILE=$3 OUTPUT=${server_log}"
	if [ -z "$VERBOSE" ]; then ($cmd > ${log});	else ($cmd); fi

	sleep 1
	printf "client\n" >> ${log}
	printf "=============================\n" >> ${log}
	($1) | ./client/client.py -p $DEFAULT_PORT >> ${log}
}

run_test()
{
	echo "Testing [${2}]"
	echo "============================="
	server_log=./test/output/manual_test_$2.log
	log=./test/log/manual_test_$2.log
	export DEFAULT_PORT=$((DEFAULT_PORT+1))

	export cmd="make server PORT=$DEFAULT_PORT FILE=$3 OUTPUT=${server_log}"
	if [ -z "$VERBOSE" ]; then ($cmd > ${log});	else ($cmd); fi

	sleep 1
	printf "client\n" >> ${log}
	printf "=============================\n" >> ${log}
	($1) | ./client/client.py -p $DEFAULT_PORT >> ${log}
	echo exit | ./client/client.py -p $DEFAULT_PORT >/dev/null
}


gcc ./test/script/signal_program.c -o ./test/script/signal
gcc ./test/script/stoptime.c -o ./test/script/stoptime
# test_tcp

test_all_yml
run_test "echo status" "status" ""

run_test "./test/script/start_stop_restart.sh" "start_stop_restart" "./test/yaml/start_stop_restart.yml"

run_test "echo exit" "exit"

run_test "echo stop signal" "signal" "./test/yaml/signal.yml"
grep received "./test/log/manual_test_signal.log" >/dev/null
if [ $? -eq 0 ] ; then test_print 0  "signal" ; else test_print 1  "signal" ; fi

#this file is also used in a script change it in both places
cp "./test/yaml/stoptime.yml" "/tmp/reload_conf.yml"
run_test  "./test/script/reload_conf.sh" "reload_conf" "/tmp/reload_conf.yml"

run_test  "./test/script/stoptime.sh" "stoptime" "./test/yaml/stoptime.yml" &

# exit_all_yml
