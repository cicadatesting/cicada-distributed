
BASE_IMAGE_NAME=cicadatesting/cicada-distributed-base-image
MANAGER_IMAGE_NAME=cicadatesting/cicada-distributed-manager

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
	pip install -r requirements.txt

# NOTE: may need to use sudo
install-dev-local:
	python3 setup.py install

install-dev-remote: install-dev-dependencies
	python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps cicadad==0.1.1

# NOTE: may need to use sudo
uninstall:
	python3 -m pip uninstall cicadad

build-base-local:
	docker build -f dockerfiles/base-image.local.dockerfile -t ${BASE_IMAGE_NAME}:latest .

build-base-dev:
	docker build -f dockerfiles/base-image.dev-a.dockerfile -t ${BASE_IMAGE_NAME}:pre-release .

build-base:
	docker build -f dockerfiles/base-image.dockerfile -t ${BASE_IMAGE_NAME}:0.1.1 .

build-manager-local:
	docker build -f dockerfiles/manager.local.dockerfile -t ${MANAGER_IMAGE_NAME}:latest .

build-manager-dev:
	docker build -f dockerfiles/manager.dev-a.dockerfile -t ${MANAGER_IMAGE_NAME}:pre-release .

build-manager:
	docker build -f dockerfiles/manager.dockerfile -t ${MANAGER_IMAGE_NAME}:0.1.1 .

clean:
	rm -r dist
	rm -r build
	rm -r src/cicadad.egg-info

clean-containers:
	docker container stop $(shell docker ps -q --filter "label=cicada-distributed") \
	&& docker container rm $(shell docker ps -q --filter "label=cicada-distributed")

proto-compile:
	cd src && python3 -m grpc_tools.protoc -I . \
		--python_out=. \
		--grpc_python_out=. \
		cicadad/protos/*.proto
