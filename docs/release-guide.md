# Release Guide

Steps for person making release to follow in order to make sure everything is
updated properly.

## Updating Cicada-Distributed

1. Checkout the `dev` branch and pull in the changes from remote
2. Search for the previously released version number to highlight changes
3. Change version number in `setup.cfg`
4. Change version number in `constants.py`
5. Change version numbers in Makefiles (root and backend)
6. Change version numbers in `.github/workflows/release-docker.yml`
7. Change version numbers in templates (`Dockerfile`, kube charts)
8. Change version numbers in `cicada-distributed-demos` (`Dockerfile` in `integration-tests`, `load-test`, and `stress-test`)

## Testing Cicada-Distributed

1. Install `cicada-distributed` locally using the `Makefile`
    - `make install-dev-local`
    - `make build-base-dev`
    - NOTE: you may need to uninstall (`make uninstall`) first or use `sudo`
2. Build the backend client in dev (`make build-dev`)
3. Start a local cluster in dev mode (`ENV=dev cicada-distributed start-cluster`)
4. Switch to the demo repo (cicada-distributed-demos) and start the API
(`make up`), then run each demo in dev mode (`make run-dev`)
5. Spin down the Docker cluster, then start a k3d cluster (`make setup-cluster`)
6. Import the images into the cluster (`import-images-dev`)
7. Install the Helm chart (`make install-kube`)
8. Spin down the example API (`make down`), then restart it in K8s
(`make import-images` + `make install-kube`)
9. Repeat the testing process for K8s (`make import-kube-dev` + `make run-kube`)

