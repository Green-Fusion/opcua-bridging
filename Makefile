test: down
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build --remove-orphans --abort-on-container-exit --exit-code-from client
up: down
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build
down:
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml down