"""Price level structure - FIFO queue at a price point."""
from collections import deque
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models import Order
else:
    # Import at runtime - automatically resolved by Python path
    try:
        from .models import Order
    except (ImportError, ValueError):
        # Fallback if relative import fails
        from models import Order


class PriceLevel:
    """Maintains FIFO queue of orders at a single price point."""

    def __init__(self, price: float):
        self.price = price
        self.orders = deque()  # FIFO queue for price-time priority
        self.total_volume = 0.0

    def add_order(self, order: Order) -> None:
        """Add order to end of queue (O(1))."""
        if order.price != self.price:
            raise ValueError(f"Order price {order.price} != level {self.price}")
        self.orders.append(order)
        self.total_volume += order.remaining_quantity

    def get_first_order(self) -> Optional[Order]:
        """Get first (oldest) order at this price level."""
        return self.orders[0] if self.orders else None

    def remove_order(self, order: Order) -> bool:
        """Remove specific order from level."""
        try:
            self.orders.remove(order)
            self.total_volume -= order.remaining_quantity
            return True
        except ValueError:
            return False

    def update_volume(self, old_remaining: float, new_remaining: float) -> None:
        """Update total volume when order is partially filled."""
        self.total_volume += (new_remaining - old_remaining)

    def is_empty(self) -> bool:
        """Check if level has no orders."""
        return len(self.orders) == 0

    def __len__(self) -> int:
        return len(self.orders)

    def __repr__(self) -> str:
        return f"PriceLevel(price={self.price}, orders={len(self.orders)}, volume={self.total_volume})"
