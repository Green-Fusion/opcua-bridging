test: down
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build --abort-on-container-exit --remove-orphans
up:
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml up --build
down:
	sudo docker-compose -f examples/bridge/docker-compose.yaml-test.yml down