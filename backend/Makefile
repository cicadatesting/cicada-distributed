.PHONY=build
BACKEND_IMAGE_NAME=cicadatesting/cicada-distributed-backend
VERSION=1.6.0

build-bin:
	env GOOS=darwin GOARCH=amd64 go build -o build/backend-darwin-amd64 github.com/cicadatesting/backend
	env GOOS=darwin GOARCH=arm64 go build -o build/backend-darwin-arm64 github.com/cicadatesting/backend
	env GOOS=linux GOARCH=amd64 go build -o build/backend-linux-amd64 github.com/cicadatesting/backend
	env GOOS=linux GOARCH=arm64 go build -o build/backend-linux-arm64 github.com/cicadatesting/backend
	env GOOS=linux GOARCH=386 go build -o build/backend-linux-32 github.com/cicadatesting/backend
	env GOOS=linux GOARCH=arm go build -o build/backend-linux-arm github.com/cicadatesting/backend
	env GOOS=windows GOARCH=amd64 go build -o build/backend-amd64.exe github.com/cicadatesting/backend

build-local:
	docker build -t ${BACKEND_IMAGE_NAME}:latest .

build-dev:
	docker build -t ${BACKEND_IMAGE_NAME}:pre-release .

build:
	docker build -t ${BACKEND_IMAGE_NAME}:${VERSION} .

run-local:
	docker run -d --rm -p 8283:8283 --network cicada-distributed-network ${BACKEND_IMAGE_NAME}:latest

proto-compile:
	protoc --go_out=. --go_opt=paths=source_relative \
		--go-grpc_out=. --go-grpc_opt=paths=source_relative \
		api/*.proto
