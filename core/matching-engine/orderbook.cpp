#include "orderbook.hpp"
#include <iostream>

OrderBook::OrderBook()
{
    best_bid = nullptr;
    best_ask = nullptr;
}

void OrderBook::add_order(Order* order)
{
    order_lookup[order->id] = order;

    std::cout << "Order added: " << order->id << std::endl;
}

void OrderBook::cancel_order(uint64_t id)
{
    auto it = order_lookup.find(id);

    if(it != order_lookup.end())
    {
        std::cout << "Order cancelled: " << id << std::endl;
        order_lookup.erase(it);
    }
}

bool OrderBook::has_match()
{
    if(best_bid && best_ask)
        return best_bid->price >= best_ask->price;

    return false;
}
