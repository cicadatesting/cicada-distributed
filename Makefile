
BASE_IMAGE_NAME=cicadatesting/cicada-distributed-base-image
BACKEND_IMAGE_NAME=cicadatesting/cicada-distributed-backend
CICADA_VERSION=1.4.2

build-bin:
	cd backend && make build-bin
	cp backend/build/* src/cicadad/backend

# NOTE: may need to use sudo
# NOTE: may be helpful to run make clean
package: build-bin
	python3 setup.py sdist bdist_wheel

upload-dev:
	python3 -m twine upload --repository testpypi dist/*

# NOTE: may need to use sudo
install-local:
	python3 -m pip install -e .

install-dev-dependencies:
	pip install -r requirements.txt

# NOTE: may need to use sudo
install-dev-local: build-bin
	python3 setup.py install

install-dev-remote: install-dev-dependencies
	python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps cicadad==${CICADA_VERSION}

# NOTE: may need to use sudo
uninstall:
	python3 -m pip uninstall cicadad

build-base-local:
	docker build -f dockerfiles/base-image.local.dockerfile -t ${BASE_IMAGE_NAME}:latest .

build-base-dev:
	docker build -f dockerfiles/base-image.dev.dockerfile -t ${BASE_IMAGE_NAME}:pre-release .

build-base:
	docker build --build-arg CICADA_VERSION=${CICADA_VERSION} \
		-f dockerfiles/base-image.dockerfile \
		-t ${BASE_IMAGE_NAME}:${CICADA_VERSION} .

setup-cluster:
	k3d cluster create -p "8283:30083@server:0"

import-images-local:
	docker tag ${BACKEND_IMAGE_NAME}:latest ${BACKEND_IMAGE_NAME}:local
	k3d image import ${BACKEND_IMAGE_NAME}:local

import-images-dev:
	docker tag ${BACKEND_IMAGE_NAME}:pre-release ${BACKEND_IMAGE_NAME}:local
	k3d image import ${BACKEND_IMAGE_NAME}:local

import-images:
	docker tag ${BACKEND_IMAGE_NAME}:${CICADA_VERSION} ${BACKEND_IMAGE_NAME}:local
	k3d image import ${BACKEND_IMAGE_NAME}:local

install-kube:
	cicada-distributed --debug start-cluster --mode=KUBE > kube-cluster/base/cicada-distributed.yaml
	kubectl apply -k kube-cluster/base
	kubectl apply -k kube-cluster/overlays/local

uninstall-kube:
	kubectl delete -k kube-cluster/base

teardown-cluster:
	k3d cluster delete

clean:
	rm -r dist
	rm -r build
	rm -r src/cicadad.egg-info

# NOTE: requires `pip install grpcio-tools`
proto-compile:
	cd src && python3 -m grpc_tools.protoc -I . \
		--python_out=. \
		--grpc_python_out=. \
		cicadad/protos/*.proto
