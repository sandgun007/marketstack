"""Unit tests for the Price-Time Priority matching algorithm."""
import pytest
from datetime import datetime, timedelta
from core.matching_engine.models import Order, OrderSide, OrderStatus
from core.matching_engine.orderbook import Orderbook
from core.matching_engine.matcher import Matcher


class TestMatcher:
    """Test matching algorithm."""

    def test_perfect_match_buy(self):
        """Test matching a buy order against a sell order."""
        book = Orderbook("BTC/USD")
        matcher = Matcher()

        # Add sell order
        sell_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=1.0,
        )
        book.add_order(sell_order)

        # Submit buy order
        buy_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )

        trades = matcher.match_order(book, buy_order)

        assert len(trades) == 1
        assert trades[0].quantity == 1.0
        assert trades[0].price == 100.0  # Seller's price
        assert sell_order.remaining_quantity == 0
        assert buy_order.remaining_quantity == 0

    def test_partial_fill(self):
        """Test partial fill when quantities don't match."""
        book = Orderbook("BTC/USD")
        matcher = Matcher()

        # Add sell order for 0.5 BTC
        sell_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=0.5,
        )
        book.add_order(sell_order)

        # Submit buy order for 1.0 BTC
        buy_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )

        trades = matcher.match_order(book, buy_order)

        assert len(trades) == 1
        assert trades[0].quantity == 0.5
        assert sell_order.remaining_quantity == 0
        assert buy_order.remaining_quantity == 0.5

    def test_no_match_price_gap(self):
        """Test no match when there's a price gap."""
        book = Orderbook("BTC/USD")
        matcher = Matcher()

        # Add sell order at 101
        sell_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=101.0,
            quantity=1.0,
        )
        book.add_order(sell_order)

        # Submit buy order at 100
        buy_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )

        trades = matcher.match_order(book, buy_order)

        assert len(trades) == 0
        # Buy order should remain in book
        assert buy_order.remaining_quantity == 1.0
        book.add_order(buy_order)
        assert len(book.bids) == 1

    def test_fifo_at_price_level(self):
        """Test FIFO matching at a price level."""
        book = Orderbook("BTC/USD")
        matcher = Matcher()

        # Add two sell orders at same price
        sell1 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=0.5,
            timestamp=datetime.utcnow(),
        )
        sell2 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=0.5,
            timestamp=datetime.utcnow() + timedelta(milliseconds=1),
        )
        book.add_order(sell1)
        book.add_order(sell2)

        # Submit buy order for 1.0
        buy_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )

        trades = matcher.match_order(book, buy_order)

        # Should match both sells
        assert len(trades) == 2
        # First trade should be with sell1 (FIFO)
        assert trades[0].seller_order_id == sell1.id
        assert trades[1].seller_order_id == sell2.id

    def test_multiple_price_levels(self):
        """Test matching across multiple price levels."""
        book = Orderbook("BTC/USD")
        matcher = Matcher()

        # Add sell orders at different prices
        sell1 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=0.3,
        )
        sell2 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=101.0,
            quantity=0.4,
        )
        sell3 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=102.0,
            quantity=0.3,
        )
        book.add_order(sell1)
        book.add_order(sell2)
        book.add_order(sell3)

        # Buy order should match best prices first
        buy_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=102.0,
            quantity=1.0,
        )

        trades = matcher.match_order(book, buy_order)

        # Should match sell1, sell2, sell3 in order (best prices first)
        assert len(trades) == 3
        assert trades[0].price == 100.0
        assert trades[1].price == 101.0
        assert trades[2].price == 102.0

    def test_sell_order_matching(self):
        """Test matching a sell order against buy orders."""
        book = Orderbook("BTC/USD")
        matcher = Matcher()

        # Add buy order
        buy_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )
        book.add_order(buy_order)

        # Submit sell order
        sell_order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=1.0,
        )

        trades = matcher.match_order(book, sell_order)

        assert len(trades) == 1
        assert trades[0].price == 100.0  # Seller's price
        assert buy_order.remaining_quantity == 0
        assert sell_order.remaining_quantity == 0
