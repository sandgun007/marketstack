#include "matching_engine.hpp"
#include <iostream>
#include <algorithm>

void MatchingEngine::match()
{
    while(book.best_bid && book.best_ask &&
          book.best_bid->price >= book.best_ask->price)
    {
        Order* buy = book.best_bid->head;
        Order* sell = book.best_ask->head;

        if(!buy || !sell)
            return;

        uint64_t trade_qty =
            std::min(buy->remaining, sell->remaining);

        double trade_price = sell->price;

        std::cout << "TRADE "
                  << "price=" << trade_price
                  << " qty=" << trade_qty
                  << std::endl;

        buy->remaining -= trade_qty;
        sell->remaining -= trade_qty;

        if(buy->remaining == 0)
        {
            remove_order(buy);
        }

        if(sell->remaining == 0)
        {
            remove_order(sell);
        }
        void MatchingEngine::remove_order(Order* order)
        {
        PriceLevel* level = order->parent;

        if(order->prev)
        order->prev->next = order->next;
                
        if(order->next)
        order->next->prev = order->prev;

        if(level->head == order)
        level->head = order->next;

        if(level->tail == order)
        level->tail = order->prev;

        book.order_lookup.erase(order->id);
        }
    }
}
