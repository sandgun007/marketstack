#pragma once

#include "order.hpp"

struct PriceLevel
{
    double price;

    Order* head;
    Order* tail;

    uint64_t total_volume;

    PriceLevel* left;
    PriceLevel* right;
};
