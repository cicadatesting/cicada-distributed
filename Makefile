
# NOTE: may need to use sudo
# NOTE: may be helpful to run make clean
package:
	python3 setup.py sdist bdist_wheel

upload-dev:
	python3 -m twine upload --repository testpypi dist/*

# NOTE: may need to use sudo
install-local:
	python3 -m pip install -e .

install-dev-dependencies:
	pip install docker \
		click \
		pydantic \
		kafka-python \
		grpcio \
		protobuf \
		dask \
		distributed \
		blessed

install-dev-local:
	python3 setup.py install

install-dev-remote: install-dev-dependencies
	python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps cicadad==0.1.0

build-base-local:
	docker build -f dockerfiles/base-image.local.dockerfile -t cicadatesting/cicada-distributed-base-image:latest .

build-base-dev:
	docker build -f dockerfiles/base-image.dev-a.dockerfile -t cicadatesting/cicada-distributed-base-image:pre-release .

build-base:
	docker build -f dockerfiles/base-image.dockerfile -t cicadatesting/cicada-distributed-base-image:latest .

build-manager-local:
	docker build -f dockerfiles/manager.local.dockerfile -t cicadatesting/cicada-distributed-manager:latest .

build-manager-dev:
	docker build -f dockerfiles/manager.dev-a.dockerfile -t cicadatesting/cicada-distributed-manager:pre-release .

build-manager:
	docker build -f dockerfiles/manager.dockerfile -t cicadatesting/cicada-distributed-manager:latest .

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
