DEFAULT_CONF_FILE=./server/taskmaster.yml
DEFAULT_LOCK_FILE=/tmp/taskmaster.lock

all: server _sleep client


_sleep:
	@sleep 1

server:
	@echo starting server...
	@killall -q python3 || true
	@rm -f $(DEFAULT_LOCK_FILE)
	@./server/server.py -f $(if $(FILE),$(FILE),$(DEFAULT_CONF_FILE)) &

client:
	@echo starting client...
	@./client/client.py || echo client has exited
	@echo exit | ./client/client.py

test:
	@./test/unit_tester.sh || test failed


.PHONY: server client test
