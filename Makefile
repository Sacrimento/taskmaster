DEFAULT_CONF_FILE=./server/taskmaster.yml
DEFAULT_LOCK_FILE=/tmp/taskmaster.lock

all: run

run:
	@rm -f $(DEFAULT_LOCK_FILE)
	@killall -q python3 || true
	@python3 server/server.py -f $(DEFAULT_CONF_FILE) &
	@sleep 1
	@python3 ./client/client.py
