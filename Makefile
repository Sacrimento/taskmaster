DEFAULT_CONF_FILE=./server/taskmaster.yml
DEFAULT_LOCK_FILE=/tmp/taskmaster.lock

all: server _sleep client


_sleep:
	sleep 1

server:
	@echo starting server...
	@rm -f $(DEFAULT_LOCK_FILE)
	@killall -q python3 || true
	@python3 server/server.py -f $(DEFAULT_CONF_FILE) &

client:
	@echo starting client...
	@python3 ./client/client.py || echo client has exited


.PHONY: server client
