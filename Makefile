DEFAULT_CONF_FILE=./server/taskmaster.yml
DEFAULT_OUTPUT_FILE=/tmp/taskmaster.log
DEFAULT_LOCK_FILE=/tmp/taskmaster.lock
DEFAULT_PORT=4242

all: server _sleep client


_sleep:
	@sleep 1

server:
	@echo starting server...
	@killall -q python3 || true
	@rm -f $(DEFAULT_LOCK_FILE)
	@./server/server.py -p $(if $(PORT),$(PORT),$(DEFAULT_PORT)) -o $(if $(OUTPUT),$(OUTPUT),$(DEFAULT_OUTPUT_FILE)) -f $(if $(FILE),$(FILE),$(DEFAULT_CONF_FILE)) &

client:
	@echo starting client...
	@./client/client.py || echo client has exited
	@echo exit | ./client/client.py

test:
	@./test/unit_tester.sh || test failed
	@killall cat stoptime signal starttime 2>/dev/null || echo process killed


.PHONY: server client test
