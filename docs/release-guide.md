# Release Guide

Steps for person making release to follow in order to make sure everything is
updated properly.

## Updating Cicada-Distributed

1. Checkout the `dev` branch and pull in the changes from remote
2. Search for the previously released version number to highlight changes
3. Change version number in `setup.cfg`
4. Change version number in `constants.py`
5. Change version numbers in Makefiles (root, container-service and
datastore-client)
6. Change version numbers in `.github/workflows/release-docker.yml`
7. Change version numbers in templates (`Dockerfile`, kube charts)
8. Change version numbers in `cicada-distributed-demos` (`Dockerfile` in `integration-tests`, `load-test`, and `stress-test`)

## Testing Cicada-Distributed

1. Install `cicada-distributed` locally using the `Makefile`
    - `make install-dev-local`
    - `make build-base-dev`
    - NOTE: you may need to uninstall (`make uninstall`) first or use `sudo`
2. Build the datastore client in dev (`make build-dev`)
3. Build the container service in dev (`make build-dev`)
4. Start a local cluster in dev mode (`ENV=dev cicada-distributed start-cluster`)
5. Switch to the demo repo (cicada-distributed-demos) and start the API, then
run each demo in dev mode (`make run-dev`)
6. Spin down the Docker cluster, then start a k3d cluster in
cicada-distributed-charts (`make setup-cluster`)
7. Import the images into the cluster (`import-images-dev`)
8. Install the Helm chart (`make install-chart`)
9. Repeat the testing process for K8s (`make import-kube-dev` + `make run-kube`)

