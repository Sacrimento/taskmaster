#!/bin/sh

run_test()
{
	make server FILE=$2 >/dev/null
	sleep 1
	OUTPUT=`$1 | ./client/client.py`
	echo $OUTPUT
	echo exit  | ./client/client.py >/dev/null
}

#status
run_test "echo status"

#start, stop, restart
run_test "echo `python -c 'print("\n".join(["start", "stop", "restart"]))'`"

##stoptime

run_test 'echo "stop stoptime\nstatus";sleep 30;echo "status"'

##startretries

#echo ""
