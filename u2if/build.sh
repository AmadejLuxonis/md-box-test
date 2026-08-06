#!/usr/bin/env bash
set -e

pushd docker
  docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) -t u2if-builder .
popd

docker run --user $(id -u):$(id -g) --rm -it -v "$PWD":/work u2if-builder bash build_in_container.sh
