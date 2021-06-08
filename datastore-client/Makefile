.PHONY=build

build:
	docker build -t cicadatesting/cicada-distributed-datastore-client:latest .

run:
	docker run -d --rm -p 50052:50052 --network cicada-distributed-network cicadatesting/cicada-distributed-datastore-client:latest

proto-compile:
	protoc --go_out=. --go_opt=paths=source_relative \
		--go-grpc_out=. --go-grpc_opt=paths=source_relative \
		api/*.proto
