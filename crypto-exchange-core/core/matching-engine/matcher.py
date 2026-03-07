"""Price-Time Priority matching algorithm."""
from typing import List, Tuple, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from models import Order, OrderSide, Trade, OrderStatus
    from orderbook import Orderbook
else:
    try:
        from .models import Order, OrderSide, Trade, OrderStatus
        from .orderbook import Orderbook
    except (ImportError, ValueError):
        from models import Order, OrderSide, Trade, OrderStatus
        from orderbook import Orderbook


class Matcher:
    """
    Implements Price-Time Priority matching:
    1. Best price gets priority
    2. Within same price level, FIFO by timestamp
    """

    def __init__(self):
        self.trades: List[Trade] = []

    def match_order(self, orderbook: Orderbook, incoming_order: Order) -> List[Trade]:
        """
        Match incoming order against orderbook.
        Returns list of trades executed.
        """
        executed_trades = []

        if incoming_order.side == OrderSide.BUY:
            executed_trades = self._match_buy_order(orderbook, incoming_order)
        else:  # SELL
            executed_trades = self._match_sell_order(orderbook, incoming_order)

        self.trades.extend(executed_trades)
        return executed_trades

    def _match_buy_order(self, orderbook: Orderbook, buy_order: Order) -> List[Trade]:
        """Match BUY order against ASK side (best asks first)."""
        trades = []

        # Iterate asks in ascending price order (best first)
        for ask_price in list(orderbook.asks.keys()):
            if buy_order.remaining_quantity <= 0:
                break

            # Stop if buy price < ask price (no match possible)
            if buy_order.price < ask_price:
                break

            ask_level = orderbook.asks[ask_price]

            # FIFO matching at this price level
            while buy_order.remaining_quantity > 0 and not ask_level.is_empty():
                sell_order = ask_level.get_first_order()
                if not sell_order:
                    break

                # Execute trade
                trade_qty = min(buy_order.remaining_quantity, sell_order.remaining_quantity)
                trade = self._execute_trade(orderbook, buy_order, sell_order, trade_qty, ask_price)
                trades.append(trade)

                # Remove fully filled orders
                if sell_order.remaining_quantity <= 0:
                    orderbook.cancel_order(sell_order.id)

            # Clean up empty ask level
            if ask_level.is_empty() and ask_price in orderbook.asks:
                del orderbook.asks[ask_price]

        return trades

    def _match_sell_order(self, orderbook: Orderbook, sell_order: Order) -> List[Trade]:
        """Match SELL order against BID side (best bids first)."""
        trades = []

        # Iterate bids in descending price order (best first) - already reversed by SortedDict
        for bid_price in list(orderbook.bids.keys()):
            if sell_order.remaining_quantity <= 0:
                break

            # Stop if sell price > bid price (no match possible)
            if sell_order.price > bid_price:
                break

            bid_level = orderbook.bids[bid_price]

            # FIFO matching at this price level
            while sell_order.remaining_quantity > 0 and not bid_level.is_empty():
                buy_order = bid_level.get_first_order()
                if not buy_order:
                    break

                # Execute trade at seller's price
                trade_qty = min(sell_order.remaining_quantity, buy_order.remaining_quantity)
                trade = self._execute_trade(orderbook, buy_order, sell_order, trade_qty, sell_order.price)
                trades.append(trade)

                # Remove fully filled orders
                if buy_order.remaining_quantity <= 0:
                    orderbook.cancel_order(buy_order.id)

            # Clean up empty bid level
            if bid_level.is_empty() and bid_price in orderbook.bids:
                del orderbook.bids[bid_price]

        return trades

    def _execute_trade(
        self,
        orderbook: Orderbook,
        buy_order: Order,
        sell_order: Order,
        trade_qty: float,
        trade_price: float,
    ) -> Trade:
        """Execute a trade between two orders."""
        # Update remaining quantities
        buy_order.remaining_quantity -= trade_qty
        sell_order.remaining_quantity -= trade_qty

        # Update order statuses
        if buy_order.remaining_quantity <= 0:
            buy_order.status = OrderStatus.FILLED
        else:
            buy_order.status = OrderStatus.PARTIALLY_FILLED

        if sell_order.remaining_quantity <= 0:
            sell_order.status = OrderStatus.FILLED
        else:
            sell_order.status = OrderStatus.PARTIALLY_FILLED

        # Create trade record
        trade = Trade.create(
            trading_pair=orderbook.trading_pair,
            buyer_order_id=buy_order.id,
            seller_order_id=sell_order.id,
            quantity=trade_qty,
            price=trade_price,
        )

        return trade

    def get_all_trades(self) -> List[Trade]:
        """Get all executed trades."""
        return self.trades.copy()
