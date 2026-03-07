#include "matching_engine.hpp"
#include "order.hpp"

int main()
{
    MatchingEngine engine;

    Order buy{1,100.0,10,10,Side::BUY,nullptr,nullptr};
    Order sell{2,99.0,10,10,Side::SELL,nullptr,nullptr};

    engine.submit_order(&buy);
    engine.submit_order(&sell);

    engine.match();

    return 0;
}
