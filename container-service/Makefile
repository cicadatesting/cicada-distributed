.PHONY=build
CONTAINER_SERVICE_IMAGE_NAME=cicadatesting/cicada-distributed-container-service

build-local:
	docker build -t ${CONTAINER_SERVICE_IMAGE_NAME}:latest .

build-dev:
	docker build -t ${CONTAINER_SERVICE_IMAGE_NAME}:pre-release .

build:
	docker build -t ${CONTAINER_SERVICE_IMAGE_NAME}:1.4.2 .

run-local:
	docker run -d --rm -p 8283:8283 --network cicada-distributed-network ${DATASTORE_IMAGE_NAME}:latest

run:
	docker run -d \
		--rm \
		--name cicada-distributed-container-service \
		-p 8284:8284 \
		--network cicada-distributed-network \
		-v /var/run/docker.sock:/var/run/docker.sock \
		cicadatesting/cicada-distributed-container-service:latest

proto-compile:
	protoc --go_out=. --go_opt=paths=source_relative \
		--go-grpc_out=. --go-grpc_opt=paths=source_relative \
		api/*.proto
