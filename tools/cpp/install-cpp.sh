#!/usr/bin/env bash
set -euo pipefail

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y \
  build-essential cmake pkg-config \
  nlohmann-json3-dev libmsgpack-dev \
  libprotobuf-dev protobuf-compiler \
  flatbuffers-compiler libflatbuffers-dev \
  capnproto libcapnp-dev \
  libyaml-cpp-dev \
  libzstd-dev zlib1g-dev liblz4-dev \
  libsnappy-dev libbrotli-dev libbz2-dev liblzma-dev
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y \
  gcc-c++ cmake pkgconfig \
  json-devel msgpack-devel \
  protobuf-devel protobuf-compiler \
  flatbuffers flatbuffers-compiler \
  capnproto capnproto-devel \
  yaml-cpp-devel \
  libzstd-devel zlib-devel lz4-devel \
  snappy-devel bzip2-devel xz-devel
else
  echo "install-cpp.sh: unsupported package manager; install C++ build deps manually" >&2
  exit 1
fi
