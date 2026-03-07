cmake_minimum_required(VERSION 3.10)

project(exchange_engine)

set(CMAKE_CXX_STANDARD 17)

add_executable(
    matching_engine
    core/matching-engine/main.cpp
    core/matching-engine/matching_engine.cpp
    core/matching-engine/orderbook.cpp
)
