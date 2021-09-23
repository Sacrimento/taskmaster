DEFAULT_CONF_FILE=./server/taskmaster.yml
DEFAULT_OUTPUT_FILE=/tmp/taskmaster.log
DEFAULT_LOCK_FILE=/tmp/taskmaster.lock
DEFAULT_PORT=4242

all: server _sleep client

_sleep:
	@sleep 1

server:
	@echo starting server...
	# @killall -q python3 || true
	@rm -f $(DEFAULT_LOCK_FILE)
	PORT=$(if $(PORT),$(PORT),$(DEFAULT_PORT))
	OUTPUT=$(if $(OUTPUT),$(OUTPUT),$(DEFAULT_OUTPUT_FILE))
	FILE=$(if $(FILE),$(FILE),$(DEFAULT_CONF_FILE))
	echo $(OUTPUT)
	@./server/server.py -p $(PORT) -l /tmp/task_master_lock_$(PORT).lock -o $(OUTPUT) -f $(FILE) &

client:
	@echo starting client...
	@./client/client.py || echo client has exited
	@echo exit | ./client/client.py

test:
	@./test/unit_tester.sh
	@killall cat stoptime signal starttime 2>/dev/null || echo process killed
	@rm -f /tmp/*.lock


.PHONY: server client test
