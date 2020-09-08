test: test-yml
up: up-yml
test-rebuild:
	sudo docker-compose -f examples/bridge/docker-compose.yml build --no-cache plc cloud client
	sudo docker-compose -f examples/bridge/docker-compose.yml up --build --exit-code-from client --abort-on-container-exit
test-yml:
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build --abort-on-container-exit --remove-orphans
up-yml:
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build
test-reliability:
	sudo docker-compose -f examples/bridge/docker-compose.reliability-test.yml up --build --remove-orphans --exit-code-from client
