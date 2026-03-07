#pragma once

#include "orderbook.hpp"

class MatchingEngine
{
private:

    OrderBook book;

public:

    void submit_order(Order* order);

    void match();
};
