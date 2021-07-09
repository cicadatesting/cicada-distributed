.PHONY=build
DATASTORE_IMAGE_NAME=cicadatesting/cicada-distributed-datastore-client

build-local:
	docker build -t ${DATASTORE_IMAGE_NAME}:latest .

build-dev:
	docker build -t ${DATASTORE_IMAGE_NAME}:pre-release .

build:
	docker build -t ${DATASTORE_IMAGE_NAME}:1.2.0 .

run-local:
	docker run -d --rm -p 8283:8283 --network cicada-distributed-network ${DATASTORE_IMAGE_NAME}:latest

proto-compile:
	protoc --go_out=. --go_opt=paths=source_relative \
		--go-grpc_out=. --go-grpc_opt=paths=source_relative \
		api/*.proto
