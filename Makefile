DEFAULT_CONF_FILE=./server/taskmaster.yml
DEFAULT_OUTPUT_FILE=/tmp/taskmaster.log
DEFAULT_LOCK_FILE=/tmp/taskmaster.lock
DEFAULT_PORT=4242

all: server _sleep client

_sleep:
	@sleep 1

$(eval PORT?=$(DEFAULT_PORT))
server:
	@echo starting server...
	$(eval OUTPUT?=$(DEFAULT_OUTPUT_FILE))
	$(eval FILE?=$(DEFAULT_CONF_FILE))
	@./server/server.py -p $(PORT) -l /tmp/task_master_lock_$(PORT).lock -o $(OUTPUT) -f $(FILE) &

client:
	@echo starting client...
	@./client/client.py -p $(PORT) || echo client has exited
	@echo exit | ./client/client.py

test:
	@rm -f /tmp/*.lock
	@killall -q python3 || true
	@./test/unit_tester.sh || echo test failed
	@killall cat stoptime signal starttime 2>/dev/null || echo process killed


.PHONY: server client test
