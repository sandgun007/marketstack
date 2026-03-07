"""Unit tests for Orderbook and PriceLevel."""
import pytest
from core.matching_engine.models import Order, OrderSide
from core.matching_engine.orderbook import Orderbook
from core.matching_engine.price_level import PriceLevel


class TestPriceLevel:
    """Test PriceLevel FIFO queue."""

    def test_price_level_creation(self):
        """Test creating a price level."""
        level = PriceLevel(100.0)
        assert level.price == 100.0
        assert level.is_empty()
        assert len(level) == 0

    def test_add_order_to_level(self):
        """Test adding orders to a price level."""
        level = PriceLevel(100.0)
        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=1.0
        )
        level.add_order(order)

        assert not level.is_empty()
        assert len(level) == 1
        assert level.total_volume == 1.0

    def test_add_order_wrong_price(self):
        """Test that adding order with wrong price raises error."""
        level = PriceLevel(100.0)
        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=99.0, quantity=1.0
        )

        with pytest.raises(ValueError):
            level.add_order(order)

    def test_get_first_order_fifo(self):
        """Test FIFO retrieval of orders."""
        level = PriceLevel(100.0)
        order1 = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=1.0
        )
        order2 = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=2.0
        )

        level.add_order(order1)
        level.add_order(order2)

        # Should get first order added (FIFO)
        first = level.get_first_order()
        assert first.id == order1.id

    def test_remove_order(self):
        """Test removing orders from level."""
        level = PriceLevel(100.0)
        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=1.0
        )
        level.add_order(order)

        assert level.total_volume == 1.0
        removed = level.remove_order(order)
        assert removed
        assert level.is_empty()
        assert level.total_volume == 0.0

    def test_update_volume(self):
        """Test updating volume when order is partially filled."""
        level = PriceLevel(100.0)
        assert level.total_volume == 0.0

        level.update_volume(0, 1.0)
        assert level.total_volume == 1.0

        level.update_volume(1.0, 0.5)
        assert level.total_volume == 0.5


class TestOrderbook:
    """Test Orderbook management."""

    def test_orderbook_creation(self):
        """Test creating an orderbook."""
        book = Orderbook("BTC/USD")
        assert book.trading_pair == "BTC/USD"
        assert len(book.bids) == 0
        assert len(book.asks) == 0

    def test_add_buy_order(self):
        """Test adding buy orders."""
        book = Orderbook("BTC/USD")
        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=1.0
        )
        book.add_order(order)

        assert len(book.bids) == 1
        assert book.get_best_bid() == 100.0

    def test_add_sell_order(self):
        """Test adding sell orders."""
        book = Orderbook("BTC/USD")
        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.SELL, price=101.0, quantity=1.0
        )
        book.add_order(order)

        assert len(book.asks) == 1
        assert book.get_best_ask() == 101.0

    def test_multiple_price_levels(self):
        """Test orderbook with multiple price levels."""
        book = Orderbook("BTC/USD")

        # Add buy orders at different prices
        for price in [100.0, 99.0, 98.0]:
            order = Order.create(
                trading_pair="BTC/USD",
                side=OrderSide.BUY,
                price=price,
                quantity=1.0,
            )
            book.add_order(order)

        assert len(book.bids) == 3
        # Best bid should be highest price
        assert book.get_best_bid() == 100.0

    def test_cancel_order(self):
        """Test cancelling an order."""
        book = Orderbook("BTC/USD")
        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=1.0
        )
        book.add_order(order)

        assert len(book.bids) == 1
        cancelled = book.cancel_order(order.id)
        assert cancelled is not None
        assert len(book.bids) == 0

    def test_cancel_nonexistent_order(self):
        """Test cancelling nonexistent order returns None."""
        book = Orderbook("BTC/USD")
        result = book.cancel_order("nonexistent-id")
        assert result is None

    def test_best_bid_ask(self):
        """Test getting best bid and ask."""
        book = Orderbook("BTC/USD")

        # Add multiple bids
        for price in [100.0, 99.0]:
            order = Order.create(
                trading_pair="BTC/USD",
                side=OrderSide.BUY,
                price=price,
                quantity=1.0,
            )
            book.add_order(order)

        # Add multiple asks
        for price in [101.0, 102.0]:
            order = Order.create(
                trading_pair="BTC/USD",
                side=OrderSide.SELL,
                price=price,
                quantity=1.0,
            )
            book.add_order(order)

        assert book.get_best_bid() == 100.0
        assert book.get_best_ask() == 101.0

    def test_get_book_snapshot(self):
        """Test getting orderbook snapshot."""
        book = Orderbook("BTC/USD")

        order = Order.create(
            trading_pair="BTC/USD", side=OrderSide.BUY, price=100.0, quantity=1.0
        )
        book.add_order(order)

        snapshot = book.get_book_snapshot()
        assert snapshot["trading_pair"] == "BTC/USD"
        assert snapshot["best_bid"] == 100.0
        assert len(snapshot["bids"]) == 1
