"""
Core data models for the matching engine.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid


class OrderSide(Enum):
    """Order side: BUY or SELL."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status throughout its lifecycle."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """
    Represents a single order in the exchange.
    Immutable after creation for consistency.
    """
    id: str
    trading_pair: str
    side: OrderSide
    price: float
    quantity: float
    remaining_quantity: float
    timestamp: datetime  # Order submission time (for FIFO matching)
    status: OrderStatus = OrderStatus.PENDING

    def __post_init__(self):
        """Validate order constraints."""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.remaining_quantity > self.quantity:
            raise ValueError(f"Remaining quantity {self.remaining_quantity} exceeds quantity {self.quantity}")

    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.remaining_quantity <= 0

    def is_active(self) -> bool:
        """Check if order can still be matched."""
        return self.status in (OrderStatus.ACTIVE, OrderStatus.PARTIALLY_FILLED)

    @staticmethod
    def create(
        trading_pair: str,
        side: OrderSide,
        price: float,
        quantity: float,
        timestamp: Optional[datetime] = None
    ) -> 'Order':
        """Factory method to create a new order."""
        return Order(
            id=str(uuid.uuid4()),
            trading_pair=trading_pair,
            side=side,
            price=price,
            quantity=quantity,
            remaining_quantity=quantity,
            timestamp=timestamp or datetime.utcnow(),
            status=OrderStatus.ACTIVE
        )


@dataclass
class Trade:
    """
    Represents an executed trade between two orders.
    """
    id: str
    trading_pair: str
    buyer_order_id: str
    seller_order_id: str
    quantity: float
    price: float  # Price at which trade occurred (seller's price)
    timestamp: datetime

    @staticmethod
    def create(
        trading_pair: str,
        buyer_order_id: str,
        seller_order_id: str,
        quantity: float,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> 'Trade':
        """Factory method to create a new trade."""
        return Trade(
            id=str(uuid.uuid4()),
            trading_pair=trading_pair,
            buyer_order_id=buyer_order_id,
            seller_order_id=seller_order_id,
            quantity=quantity,
            price=price,
            timestamp=timestamp or datetime.utcnow()
        )


@dataclass
class OrderBookSnapshot:
    """
    Snapshot of orderbook state at a specific point in time.
    Used for market data queries.
    """
    trading_pair: str
    timestamp: datetime
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    bids: list = field(default_factory=list)  # [(price, quantity), ...]
    asks: list = field(default_factory=list)  # [(price, quantity), ...]
