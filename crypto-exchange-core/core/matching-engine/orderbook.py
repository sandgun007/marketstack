"""Orderbook management with buy/sell sides."""
from sortedcontainers import SortedDict
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from models import Order, OrderSide
    from price_level import PriceLevel
else:
    try:
        from .models import Order, OrderSide
        from .price_level import PriceLevel
    except (ImportError, ValueError):
        from models import Order, OrderSide
        from price_level import PriceLevel


class Orderbook:
    """
    Manages buy and sell sides of an orderbook for a single trading pair.
    Uses SortedDict for O(log n) price level lookup.
    """

    def __init__(self, trading_pair: str):
        self.trading_pair = trading_pair
        # Bids: price descending (highest first) - use negative key
        self.bids = SortedDict(lambda x: -x)
        # Asks: price ascending (lowest first)
        self.asks = SortedDict()
        # Fast lookup by order ID: order_id -> (side, price)
        self.order_map: Dict[str, Tuple[str, float]] = {}

    def add_order(self, order: Order) -> None:
        """Add order to appropriate side."""
        if order.trading_pair != self.trading_pair:
            raise ValueError(f"Order pair {order.trading_pair} != {self.trading_pair}")

        side = "bids" if order.side == OrderSide.BUY else "asks"
        book = self.bids if order.side == OrderSide.BUY else self.asks

        if order.price not in book:
            book[order.price] = PriceLevel(order.price)

        book[order.price].add_order(order)
        self.order_map[order.id] = (side, order.price)

    def cancel_order(self, order_id: str) -> Optional[Order]:
        """Remove order from book. Returns the order if found."""
        if order_id not in self.order_map:
            return None

        side, price = self.order_map.pop(order_id)
        book = self.bids if side == "bids" else self.asks
        level = book.get(price)

        if level:
            for order in level.orders:
                if order.id == order_id:
                    level.remove_order(order)
                    # Clean up empty price levels
                    if level.is_empty():
                        del book[price]
                    return order
        return None

    def get_best_bid(self) -> Optional[float]:
        """Return best bid price."""
        if not self.bids:
            return None
        return self.bids.keys()[0]

    def get_best_ask(self) -> Optional[float]:
        """Return best ask price."""
        if not self.asks:
            return None
        return self.asks.keys()[0]

    def get_bid_at_price(self, price: float) -> Optional[PriceLevel]:
        """Get price level on bid side."""
        return self.bids.get(price)

    def get_ask_at_price(self, price: float) -> Optional[PriceLevel]:
        """Get price level on ask side."""
        return self.asks.get(price)

    def get_book_snapshot(self, depth: int = 20) -> Dict:
        """Get current orderbook snapshot (top N levels)."""
        bids = []
        asks = []

        for i, price in enumerate(self.bids.keys()):
            if i >= depth:
                break
            level = self.bids[price]
            bids.append({"price": price, "quantity": level.total_volume})

        for i, price in enumerate(self.asks.keys()):
            if i >= depth:
                break
            level = self.asks[price]
            asks.append({"price": price, "quantity": level.total_volume})

        return {
            "trading_pair": self.trading_pair,
            "best_bid": self.get_best_bid(),
            "best_ask": self.get_best_ask(),
            "bids": bids,
            "asks": asks,
        }

    def __repr__(self) -> str:
        return f"Orderbook({self.trading_pair}, bids={len(self.bids)}, asks={len(self.asks)})"
