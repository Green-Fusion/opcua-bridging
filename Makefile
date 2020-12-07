test: down
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build --remove-orphan --abort-on-container-exit
up: down
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build
down:
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml down