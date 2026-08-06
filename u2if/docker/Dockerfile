FROM ubuntu:20.04

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    cmake \
    make \
    ninja-build \
    python3 \
    python3-pip \
    build-essential \
    gcc \
    g++ \
    gcc-arm-none-eabi \
    libnewlib-arm-none-eabi \
    libstdc++-arm-none-eabi-newlib \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid ${GROUP_ID} builder && \
    adduser --disabled-password --gecos '' --uid ${USER_ID} --gid ${GROUP_ID} --shell /bin/bash builder && \
    mkdir -p /work && \
    chown builder:builder /work

USER builder
WORKDIR /work
