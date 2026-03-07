#!/bin/bash

set -e

PROJECT_ROOT=$(pwd)

echo "Starting build process"

mkdir -p build
cd build

echo "Running CMake"
cmake $PROJECT_ROOT

echo "Compiling engine"
make -j$(nproc)

echo "Running engine"
./matching_engine
