"""Event definitions for event sourcing."""
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from models import Order, Trade
else:
    try:
        from .models import Order, Trade
    except (ImportError, ValueError):
        from models import Order, Trade


class EventType(Enum):
    """Types of events in the matching engine."""
    ORDER_PLACED = "ORDER_PLACED"
    ORDER_MATCHED = "ORDER_MATCHED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_UPDATED = "ORDER_UPDATED"


@dataclass
class Event:
    """Base event class."""
    id: str
    event_type: EventType
    trading_pair: str
    timestamp: datetime
    order_id: str
    details: Dict[str, Any]

    @staticmethod
    def create(
        event_type: EventType,
        trading_pair: str,
        order_id: str,
        details: Dict[str, Any],
        timestamp: datetime = None,
    ) -> "Event":
        """Factory method to create an event."""
        return Event(
            id=str(uuid.uuid4()),
            event_type=event_type,
            trading_pair=trading_pair,
            timestamp=timestamp or datetime.utcnow(),
            order_id=order_id,
            details=details,
        )


@dataclass
class OrderPlacedEvent(Event):
    """Event: Order placed on orderbook."""

    @staticmethod
    def from_order(order: Order) -> "OrderPlacedEvent":
        """Create event from order."""
        event = Event.create(
            event_type=EventType.ORDER_PLACED,
            trading_pair=order.trading_pair,
            order_id=order.id,
            timestamp=order.timestamp,
            details={
                "side": order.side.value,
                "price": order.price,
                "quantity": order.quantity,
            },
        )
        return OrderPlacedEvent(**asdict(event))


@dataclass
class OrderMatchedEvent(Event):
    """Event: Trade executed."""

    @staticmethod
    def from_trade(trade: Trade) -> "OrderMatchedEvent":
        """Create event from trade."""
        event = Event.create(
            event_type=EventType.ORDER_MATCHED,
            trading_pair=trade.trading_pair,
            order_id=trade.buyer_order_id,  # Link to buyer
            timestamp=trade.timestamp,
            details={
                "trade_id": trade.id,
                "buyer_order_id": trade.buyer_order_id,
                "seller_order_id": trade.seller_order_id,
                "quantity": trade.quantity,
                "price": trade.price,
            },
        )
        return OrderMatchedEvent(**asdict(event))


@dataclass
class OrderCancelledEvent(Event):
    """Event: Order cancelled."""

    @staticmethod
    def create_from_order_id(
        trading_pair: str, order_id: str, timestamp: datetime = None
    ) -> "OrderCancelledEvent":
        """Create cancellation event."""
        event = Event.create(
            event_type=EventType.ORDER_CANCELLED,
            trading_pair=trading_pair,
            order_id=order_id,
            timestamp=timestamp or datetime.utcnow(),
            details={},
        )
        return OrderCancelledEvent(**asdict(event))


@dataclass
class OrderUpdatedEvent(Event):
    """Event: Order quantity updated."""

    @staticmethod
    def create_update(
        trading_pair: str,
        order_id: str,
        old_quantity: float,
        new_quantity: float,
        timestamp: datetime = None,
    ) -> "OrderUpdatedEvent":
        """Create update event."""
        event = Event.create(
            event_type=EventType.ORDER_UPDATED,
            trading_pair=trading_pair,
            order_id=order_id,
            timestamp=timestamp or datetime.utcnow(),
            details={
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
            },
        )
        return OrderUpdatedEvent(**asdict(event))
