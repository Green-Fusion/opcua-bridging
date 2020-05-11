test:
	sudo docker-compose -f docker-compose.yml up --build --exit-code-from client --abort-on-container-exit
up:
	sudo docker-compose -f docker-compose.yml up --build