#pragma once

#include "price_level.hpp"
#include <unordered_map>

class OrderBook
{
public:

    PriceLevel* best_bid;
    PriceLevel* best_ask;

    std::unordered_map<uint64_t, Order*> order_lookup;

    OrderBook();

    void add_order(Order* order);

    void cancel_order(uint64_t id);

    bool has_match();
};
