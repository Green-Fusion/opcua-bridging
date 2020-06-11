test:
	sudo docker-compose -f examples/bridge/docker-compose.yml up --build --exit-code-from client --abort-on-container-exit
up:
	sudo docker-compose -f examples/bridge/docker-compose.yml up --build
test-rebuild:
	sudo docker-compose -f examples/bridge/docker-compose.yml build --no-cache plc cloud client
	sudo docker-compose -f examples/bridge/docker-compose.yml up --build --exit-code-from client --abort-on-container-exit
