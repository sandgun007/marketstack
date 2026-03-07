#pragma once

#include <cstdint>

enum class Side
{
    BUY,
    SELL
};

struct Order
{
    uint64_t id;
    double price;
    uint64_t quantity;
    uint64_t remaining;
    Side side;

    Order* next;
    Order* prev;
};
