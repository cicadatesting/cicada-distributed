
package:
	python3 setup.py sdist bdist_wheel

# NOTE: may need to use sudo
install-local:
	python3 -m pip install -e .

build-manager-local:
	docker build -f dockerfiles/manager.local.dockerfile -t cicada-distributed-manager .

build-manager-dev:
	docker build -f dockerfiles/manager.dev.dockerfile -t cicada-distributed-manager .

build-base-local:
	docker build -f dockerfiles/base-image.local.dockerfile -t cicadatesting/cicada-distributed-base-image:latest .

build-base-dev:
	docker build -f dockerfiles/base-image.dev.dockerfile -t cicadatesting/cicada-distributed-base-image:latest .

run-manager:
	docker run \
		--rm \
		--network cicada-distributed_default \
		-v /var/run/docker.sock:/var/run/docker.sock \
		cicada-distributed-manager

clean:
	rm -r dist
	rm -r build
	rm -r src/cicadad.egg-info

clean-containers:
	docker container stop $(shell docker ps -q --filter "label=cicada-distributed") \
	&& docker container rm $(shell docker ps -q --filter "label=cicada-distributed")

services:
	docker-compose up -d

services-down:
	docker-compose down --remove-orphans

proto-compile:
	cd src && python3 -m grpc_tools.protoc -I . \
		--python_out=. \
		--grpc_python_out=. \
		cicadad/protos/*.proto
