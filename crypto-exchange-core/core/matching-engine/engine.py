"""Central matching engine - manages multiple orderbooks and coordinates matching."""
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from models import Order, Trade, OrderStatus
    from orderbook import Orderbook
    from matcher import Matcher
    from event_store import EventStore
    from events import (
        OrderPlacedEvent,
        OrderMatchedEvent,
        OrderCancelledEvent,
        OrderUpdatedEvent,
    )
else:
    try:
        from .models import Order, Trade, OrderStatus
        from .orderbook import Orderbook
        from .matcher import Matcher
        from .event_store import EventStore
        from .events import (
            OrderPlacedEvent,
            OrderMatchedEvent,
            OrderCancelledEvent,
            OrderUpdatedEvent,
        )
    except (ImportError, ValueError):
        from models import Order, Trade, OrderStatus
        from orderbook import Orderbook
        from matcher import Matcher
        from event_store import EventStore
        from events import (
            OrderPlacedEvent,
            OrderMatchedEvent,
            OrderCancelledEvent,
            OrderUpdatedEvent,
        )


class MatchingEngine:
    """
    Central engine managing multiple trading pair orderbooks.
    Single-threaded to ensure deterministic matching.
    """

    def __init__(self):
        self.orderbooks: Dict[str, Orderbook] = {}
        self.matcher = Matcher()
        self.event_store = EventStore()

    def submit_order(self, order: Order) -> List[Trade]:
        """
        Submit an order for matching.
        Returns list of trades immediately executed.
        """
        # Validate order
        if order.quantity <= 0 or order.price <= 0:
            raise ValueError("Invalid order: price and quantity must be positive")

        # Ensure orderbook exists
        if order.trading_pair not in self.orderbooks:
            self.orderbooks[order.trading_pair] = Orderbook(order.trading_pair)

        # Record event
        order_event = OrderPlacedEvent.from_order(order)
        self.event_store.append(order_event)

        # Get orderbook
        book = self.orderbooks[order.trading_pair]

        # Match against existing orders
        trades = self.matcher.match_order(book, order)

        # Record trade events
        for trade in trades:
            trade_event = OrderMatchedEvent.from_trade(trade)
            self.event_store.append(trade_event)

        # If order not fully filled, add to orderbook
        if order.remaining_quantity > 0:
            order.status = OrderStatus.PARTIALLY_FILLED if trades else OrderStatus.ACTIVE
            book.add_order(order)
        else:
            order.status = OrderStatus.FILLED

        return trades

    def cancel_order(self, trading_pair: str, order_id: str) -> bool:
        """
        Cancel an existing order.
        Returns True if order was found and cancelled.
        """
        if trading_pair not in self.orderbooks:
            return False

        book = self.orderbooks[trading_pair]
        cancelled_order = book.cancel_order(order_id)

        if cancelled_order:
            cancelled_order.status = OrderStatus.CANCELLED
            # Record cancellation event
            cancel_event = OrderCancelledEvent.create_from_order_id(
                trading_pair, order_id
            )
            self.event_store.append(cancel_event)
            return True

        return False

    def update_order_quantity(
        self, trading_pair: str, order_id: str, new_quantity: float
    ) -> bool:
        """
        Update order quantity (cancel + re-submit at new quantity).
        Returns True if successful.
        """
        if trading_pair not in self.orderbooks:
            return False

        book = self.orderbooks[trading_pair]
        existing_order = book.cancel_order(order_id)

        if not existing_order:
            return False

        old_quantity = existing_order.quantity

        # Record update event
        update_event = OrderUpdatedEvent.create_update(trading_pair, order_id, old_quantity, new_quantity)
        self.event_store.append(update_event)

        # Create new order with updated quantity
        existing_order.quantity = new_quantity
        existing_order.remaining_quantity = new_quantity

        # Re-submit at original price
        trades = self.matcher.match_order(book, existing_order)

        for trade in trades:
            trade_event = OrderMatchedEvent.from_trade(trade)
            self.event_store.append(trade_event)

        # If not fully filled, add back to book
        if existing_order.remaining_quantity > 0:
            existing_order.status = (
                OrderStatus.PARTIALLY_FILLED if trades else OrderStatus.ACTIVE
            )
            book.add_order(existing_order)
        else:
            existing_order.status = OrderStatus.FILLED

        return True

    def get_orderbook(self, trading_pair: str) -> Optional[Orderbook]:
        """Get orderbook for a trading pair."""
        return self.orderbooks.get(trading_pair)

    def get_orderbook_snapshot(self, trading_pair: str, depth: int = 20) -> Optional[Dict]:
        """Get current orderbook snapshot."""
        if trading_pair not in self.orderbooks:
            return None
        return self.orderbooks[trading_pair].get_book_snapshot(depth)

    def get_trades(self, trading_pair: Optional[str] = None) -> List[Trade]:
        """Get all executed trades, optionally filtered by trading pair."""
        if trading_pair:
            return [t for t in self.matcher.get_all_trades() if t.trading_pair == trading_pair]
        return self.matcher.get_all_trades()

    def get_trading_pairs(self) -> List[str]:
        """Get list of all active trading pairs."""
        return list(self.orderbooks.keys())

    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            "trading_pairs": len(self.orderbooks),
            "total_trades": len(self.matcher.get_all_trades()),
            "events_recorded": self.event_store.event_count,
            "active_pairs": self.get_trading_pairs(),
        }

    def __repr__(self) -> str:
        return f"MatchingEngine(pairs={len(self.orderbooks)}, trades={len(self.matcher.get_all_trades())})"
