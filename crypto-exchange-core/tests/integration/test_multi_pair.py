"""Integration tests for multi-pair and event sourcing."""
import pytest
from datetime import datetime
from core.matching_engine.models import Order, OrderSide
from core.matching_engine.engine import MatchingEngine
from core.matching_engine.replay_engine import ReplayEngine


class TestMultiPair:
    """Test multi-pair support in engine."""

    def test_multiple_trading_pairs(self):
        """Test engine managing multiple trading pairs."""
        engine = MatchingEngine()

        # Submit orders on different pairs
        btc_buy = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        eth_buy = Order.create(
            trading_pair="ETH/USD",
            side=OrderSide.BUY,
            price=3000.0,
            quantity=10.0,
        )

        engine.submit_order(btc_buy)
        engine.submit_order(eth_buy)

        assert len(engine.get_trading_pairs()) == 2
        assert "BTC/USD" in engine.get_trading_pairs()
        assert "ETH/USD" in engine.get_trading_pairs()

    def test_order_isolation_by_pair(self):
        """Test that orders on different pairs don't affect each other."""
        engine = MatchingEngine()

        # Buy at one price on BTC
        btc_buy = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        # Sell at different price on ETH
        eth_sell = Order.create(
            trading_pair="ETH/USD",
            side=OrderSide.SELL,
            price=3000.0,
            quantity=10.0,
        )

        trades_btc = engine.submit_order(btc_buy)
        trades_eth = engine.submit_order(eth_sell)

        # No trades should occur (different pairs)
        assert len(trades_btc) == 0
        assert len(trades_eth) == 0

    def test_cross_pair_trades(self):
        """Test executing trades on different pairs."""
        engine = MatchingEngine()

        # Match on BTC
        btc_sell = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=50000.0,
            quantity=1.0,
        )
        engine.submit_order(btc_sell)

        btc_buy = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        trades_btc = engine.submit_order(btc_buy)

        # Match on ETH
        eth_sell = Order.create(
            trading_pair="ETH/USD",
            side=OrderSide.SELL,
            price=3000.0,
            quantity=10.0,
        )
        engine.submit_order(eth_sell)

        eth_buy = Order.create(
            trading_pair="ETH/USD",
            side=OrderSide.BUY,
            price=3000.0,
            quantity=10.0,
        )
        trades_eth = engine.submit_order(eth_buy)

        assert len(trades_btc) == 1
        assert len(trades_eth) == 1
        assert engine.get_stats()["total_trades"] == 2


class TestEventSourcing:
    """Test event sourcing and replay."""

    def test_event_recording(self):
        """Test that events are recorded."""
        engine = MatchingEngine()

        order1 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )
        engine.submit_order(order1)

        events = engine.event_store.get_events()
        assert len(events) >= 1

    def test_event_replay_single_order(self):
        """Test replaying events to rebuild state."""
        engine = MatchingEngine()

        # Submit and match orders
        sell = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=1.0,
        )
        engine.submit_order(sell)

        buy = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )
        engine.submit_order(buy)

        # Verify trades
        trades_before = engine.get_trades()
        assert len(trades_before) == 1

        # Replay from events
        replay_engine = ReplayEngine()
        rebuilt_books = replay_engine.replay_events(engine.event_store)

        # Check rebuilt state
        assert "BTC/USD" in rebuilt_books
        rebuilt_book = rebuilt_books["BTC/USD"]
        assert len(rebuilt_book.bids) == 0
        assert len(rebuilt_book.asks) == 0

    def test_event_replay_partial_fill(self):
        """Test replaying events with partial fills."""
        engine = MatchingEngine()

        # Sell 1.0
        sell = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=100.0,
            quantity=1.0,
        )
        engine.submit_order(sell)

        # Buy 0.5 (partial fill)
        buy = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=0.5,
        )
        engine.submit_order(buy)

        # Replay
        replay_engine = ReplayEngine()
        rebuilt_books = replay_engine.replay_events(engine.event_store)

        # Should have sell order with 0.5 remaining
        book = rebuilt_books["BTC/USD"]
        assert len(book.asks) == 1
        ask_level = book.asks[100.0]
        assert ask_level.total_volume == 0.5

    def test_event_replay_with_cancellation(self):
        """Test replaying events including cancellations."""
        engine = MatchingEngine()

        # Place order
        order = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=100.0,
            quantity=1.0,
        )
        engine.submit_order(order)

        # Cancel it
        engine.cancel_order("BTC/USD", order.id)

        # Replay
        replay_engine = ReplayEngine()
        rebuilt_books = replay_engine.replay_events(engine.event_store)

        # Should be empty after replay
        book = rebuilt_books.get("BTC/USD")
        if book:
            assert len(book.bids) == 0
            assert len(book.asks) == 0


class TestEngineIntegration:
    """Integration tests for full engine workflow."""

    def test_full_order_lifecycle(self):
        """Test complete order lifecycle: place -> match -> fill."""
        engine = MatchingEngine()

        # Place sell order
        sell = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.SELL,
            price=50000.0,
            quantity=1.0,
        )
        engine.submit_order(sell)

        # Place buy order (should match)
        buy = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        trades = engine.submit_order(buy)

        # Verify trade
        assert len(trades) == 1
        assert trades[0].quantity == 1.0
        assert trades[0].price == 50000.0

    def test_cancel_and_resubmit(self):
        """Test cancelling and resubmitting orders."""
        engine = MatchingEngine()

        # Place buy order
        buy1 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50000.0,
            quantity=1.0,
        )
        engine.submit_order(buy1)

        # Cancel it
        cancelled = engine.cancel_order("BTC/USD", buy1.id)
        assert cancelled

        # Place new buy order
        buy2 = Order.create(
            trading_pair="BTC/USD",
            side=OrderSide.BUY,
            price=50001.0,
            quantity=1.0,
        )
        engine.submit_order(buy2)

        # Book should have only buy2
        book = engine.get_orderbook("BTC/USD")
        assert len(book.bids) == 1
        assert book.get_best_bid() == 50001.0
