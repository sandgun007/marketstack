"""Event replay engine - rebuild orderbook state from events."""
from typing import Dict, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from models import Order, OrderSide, OrderStatus
    from orderbook import Orderbook
    from events import Event, EventType
    from event_store import EventStore
else:
    try:
        from .models import Order, OrderSide, OrderStatus
        from .orderbook import Orderbook
        from .events import Event, EventType
        from .event_store import EventStore
    except (ImportError, ValueError):
        from models import Order, OrderSide, OrderStatus
        from orderbook import Orderbook
        from events import Event, EventType
        from event_store import EventStore


class ReplayEngine:
    """Rebuilds orderbook state by replaying events."""

    def __init__(self):
        self.orderbooks: Dict[str, Orderbook] = {}
        self.orders: Dict[str, Order] = {}  # order_id -> Order

    def replay_events(self, event_store: EventStore) -> Dict[str, Orderbook]:
        """
        Replay all events to rebuild orderbook state.
        Returns dict of trading pair -> Orderbook.
        """
        self.orderbooks.clear()
        self.orders.clear()

        for event in event_store.get_events():
            self._process_event(event)

        return self.orderbooks

    def replay_events_until(
        self, event_store: EventStore, until_timestamp: datetime
    ) -> Dict[str, Orderbook]:
        """Replay events up to a specific timestamp."""
        self.orderbooks.clear()
        self.orders.clear()

        for event in event_store.get_events():
            if event.timestamp > until_timestamp:
                break
            self._process_event(event)

        return self.orderbooks

    def _process_event(self, event: Event) -> None:
        """Process a single event."""
        if event.event_type == EventType.ORDER_PLACED:
            self._handle_order_placed(event)
        elif event.event_type == EventType.ORDER_MATCHED:
            self._handle_order_matched(event)
        elif event.event_type == EventType.ORDER_CANCELLED:
            self._handle_order_cancelled(event)
        elif event.event_type == EventType.ORDER_UPDATED:
            self._handle_order_updated(event)

    def _handle_order_placed(self, event: Event) -> None:
        """Reconstruct ORDER_PLACED event."""
        pair = event.trading_pair

        # Ensure orderbook exists
        if pair not in self.orderbooks:
            self.orderbooks[pair] = Orderbook(pair)

        # Reconstruct order
        side = OrderSide.BUY if event.details["side"] == "BUY" else OrderSide.SELL
        order = Order(
            id=event.order_id,
            trading_pair=pair,
            side=side,
            price=event.details["price"],
            quantity=event.details["quantity"],
            remaining_quantity=event.details["quantity"],
            timestamp=event.timestamp,
            status=OrderStatus.ACTIVE,
        )

        # Add to orderbook
        self.orderbooks[pair].add_order(order)
        self.orders[order.id] = order

    def _handle_order_matched(self, event: Event) -> None:
        """Reconstruct ORDER_MATCHED event."""
        pair = event.trading_pair

        if pair not in self.orderbooks:
            self.orderbooks[pair] = Orderbook(pair)

        buyer_id = event.details["buyer_order_id"]
        seller_id = event.details["seller_order_id"]
        quantity = event.details["quantity"]

        # Update buyer order
        if buyer_id in self.orders:
            buyer = self.orders[buyer_id]
            buyer.remaining_quantity -= quantity
            if buyer.remaining_quantity <= 0:
                buyer.status = OrderStatus.FILLED
            else:
                buyer.status = OrderStatus.PARTIALLY_FILLED

        # Update seller order
        if seller_id in self.orders:
            seller = self.orders[seller_id]
            seller.remaining_quantity -= quantity
            if seller.remaining_quantity <= 0:
                seller.status = OrderStatus.FILLED
            else:
                seller.status = OrderStatus.PARTIALLY_FILLED

    def _handle_order_cancelled(self, event: Event) -> None:
        """Reconstruct ORDER_CANCELLED event."""
        pair = event.trading_pair

        if pair in self.orderbooks:
            cancelled = self.orderbooks[pair].cancel_order(event.order_id)
            if cancelled:
                cancelled.status = OrderStatus.CANCELLED
                if event.order_id in self.orders:
                    del self.orders[event.order_id]

    def _handle_order_updated(self, event: Event) -> None:
        """Reconstruct ORDER_UPDATED event."""
        if event.order_id in self.orders:
            order = self.orders[event.order_id]
            # Adjust remaining quantity
            old_qty = event.details["old_quantity"]
            new_qty = event.details["new_quantity"]
            delta = new_qty - old_qty
            order.remaining_quantity += delta
            order.quantity = new_qty

    def get_orderbook_at(
        self, event_store: EventStore, timestamp: datetime
    ) -> Dict[str, Orderbook]:
        """Get orderbook state at a specific point in time."""
        return self.replay_events_until(event_store, timestamp)
