"""Unit tests for Order models and data structures."""
import pytest
from datetime import datetime
from core.matching_engine.models import Order, Trade, OrderSide, OrderStatus


class TestOrderModel:
    """Test Order dataclass."""

    def test_order_creation(self):
        """Test creating a valid order."""
        order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        assert order.trading_pair == "BTC/USD"
        assert order.side == OrderSide.BUY
        assert order.price == 50000.0
        assert order.quantity == 1.0
        assert order.remaining_quantity == 1.0
        assert order.status == OrderStatus.ACTIVE

    def test_order_invalid_price(self):
        """Test that negative price raises error."""
        with pytest.raises(ValueError):
            Order.create(
                trading_pair="BTC/USD",
                side=OrderSide.BUY,
                price=-100.0,
                quantity=1.0,
            )

    def test_order_invalid_quantity(self):
        """Test that negative quantity raises error."""
        with pytest.raises(ValueError):
            Order.create(
                trading_pair="BTC/USD",
                side=OrderSide.BUY,
                price=50000.0,
                quantity=-1.0,
            )

    def test_order_is_filled(self):
        """Test is_filled() method."""
        order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        assert not order.is_filled()

        order.remaining_quantity = 0
        assert order.is_filled()

    def test_order_is_active(self):
        """Test is_active() method."""
        order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        assert order.is_active()

        order.status = OrderStatus.CANCELLED
        assert not order.is_active()

    def test_order_timestamp(self):
        """Test order timestamp logic."""
        now = datetime.utcnow()
        order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
            timestamp=now,
        )
        assert order.timestamp == now

    def test_order_unique_ids(self):
        """Test that orders have unique IDs."""
        order1 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        order2 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        assert order1.id != order2.id


class TestTradeModel:
    """Test Trade dataclass."""

    def test_trade_creation(self):
        """Test creating a valid trade."""
        trade = Trade.create(
            trading_pair="BTC/USD",
            buyer_order_id="buyer-123",
            seller_order_id="seller-123",
            quantity=1.0,
            price=50000.0,
        )
        assert trade.trading_pair == "BTC/USD"
        assert trade.buyer_order_id == "buyer-123"
        assert trade.seller_order_id == "seller-123"
        assert trade.quantity == 1.0
        assert trade.price == 50000.0

    def test_trade_unique_ids(self):
        """Test that trades have unique IDs."""
        trade1 = Trade.create(
            trading_pair="BTC/USD",
            buyer_order_id="buyer-123",
            seller_order_id="seller-123",
            quantity=1.0,
            price=50000.0,
        )
        trade2 = Trade.create(
            trading_pair="BTC/USD",
            buyer_order_id="buyer-123",
            seller_order_id="seller-123",
            quantity=1.0,
            price=50000.0,
        )
        assert trade1.id != trade2.id
