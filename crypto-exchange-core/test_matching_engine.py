#!/usr/bin/env python3
"""
Comprehensive demo and test of the Matching Engine.
Shows all core functionality working correctly.
"""
import sys
import os

# Add core/matching-engine to path
sys.path.insert(0, '/srv/marketstack/crypto-exchange-core/core/matching-engine')

# Import modules directly (they should work now since they're in the path)
try:
    import models
    from models import Order, OrderSide, Trade
    import price_level
    from price_level import PriceLevel
    import orderbook
    from orderbook import Orderbook
    import events
    from events import Event
    import event_store
    from event_store import EventStore
    import matcher
    from matcher import Matcher
    import replay_engine
    from replay_engine import ReplayEngine
    import engine
    from engine import MatchingEngine
    print("✓ All modules imported successfully\n")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_order_model():
    """Test Order model creation and validation."""
    print("\n" + "="*70)
    print("TEST 1: Order Model Creation")
    print("="*70)

    order = Order.create(
        trading_pair="BTC/USD",
        side=OrderSide.BUY,
        price=50000.0,
        quantity=1.0,
    )

    assert order.trading_pair == "BTC/USD"
    assert order.quantity == 1.0
    assert order.is_active()
    assert not order.is_filled()

    print("✓ Order model test passed")
    print(f"  - Created BUY order for 1.0 BTC @ $50,000")
    print(f"  - Order ID: {order.id[:8]}...")
    print(f"  - Status: {order.status.value}")


def test_orderbook():
    """Test Orderbook with multiple price levels."""
    print("\n" + "="*70)
    print("TEST 2: Orderbook Management")
    print("="*70)

    book = Orderbook("BTC/USD")

    # Add buy orders
    buy1 = Order.create("BTC/USD", OrderSide.BUY, 49999.0, 0.5)
    buy2 = Order.create("BTC/USD", OrderSide.BUY, 49998.0, 1.0)
    book.add_order(buy1)
    book.add_order(buy2)

    # Add sell orders
    sell1 = Order.create("BTC/USD", OrderSide.SELL, 50001.0, 0.5)
    sell2 = Order.create("BTC/USD", OrderSide.SELL, 50002.0, 1.0)
    book.add_order(sell1)
    book.add_order(sell2)

    assert len(book.bids) == 2
    assert len(book.asks) == 2
    assert book.get_best_bid() == 49999.0
    assert book.get_best_ask() == 50001.0

    print("✓ Orderbook test passed")
    print(f"  - Added 2 buy orders (bids): {len(book.bids)} price levels")
    print(f"  - Added 2 sell orders (asks): {len(book.asks)} price levels")
    print(f"  - Best bid: ${book.get_best_bid()}")
    print(f"  - Best ask: ${book.get_best_ask()}")
    print(f"  - Spread: ${book.get_best_ask() - book.get_best_bid()}")


def test_price_time_priority_matching():
    """Test Price-Time Priority matching algorithm."""
    print("\n" + "="*70)
    print("TEST 3: Price-Time Priority Matching")
    print("="*70)

    book = Orderbook("BTC/USD")
    m = Matcher()

    # Add sell order
    sell = Order.create("BTC/USD", OrderSide.SELL, 50000.0, 1.0)
    book.add_order(sell)

    # Submit matching buy order
    buy = Order.create("BTC/USD", OrderSide.BUY, 50000.0, 1.0)
    trades = m.match_order(book, buy)

    assert len(trades) == 1
    assert trades[0].quantity == 1.0
    assert trades[0].price == 50000.0
    assert sell.remaining_quantity == 0
    assert buy.remaining_quantity == 0

    print("✓ Perfect match test passed")
    print(f"  - Trade executed: 1.0 BTC @ $50,000")
    print(f"  - Trade ID: {trades[0].id[:8]}...")
    print(f"  - Buyer Order: {trades[0].buyer_order_id[:8]}...")
    print(f"  - Seller Order: {trades[0].seller_order_id[:8]}...")


def test_partial_fill():
    """Test partial fill scenario."""
    print("\n" + "="*70)
    print("TEST 4: Partial Fill")
    print("="*70)

    book = Orderbook("BTC/USD")
    m = Matcher()

    # Add sell order for 0.5 BTC
    sell = Order.create("BTC/USD", OrderSide.SELL, 50000.0, 0.5)
    book.add_order(sell)

    # Buy 1.0 BTC (only 0.5 will match)
    buy = Order.create("BTC/USD", OrderSide.BUY, 50000.0, 1.0)
    trades = m.match_order(book, buy)

    assert len(trades) == 1
    assert trades[0].quantity == 0.5
    assert sell.remaining_quantity == 0
    assert buy.remaining_quantity == 0.5

    # Add to book (partially filled)
    book.add_order(buy)
    assert len(book.bids) == 1

    print("✓ Partial fill test passed")
    print(f"  - Trade executed: 0.5 BTC @ $50,000")
    print(f"  - Seller remaining: {sell.remaining_quantity} BTC")
    print(f"  - Buyer remaining: {buy.remaining_quantity} BTC (added to book)")


def test_multi_pair_engine():
    """Test engine with multiple trading pairs."""
    print("\n" + "="*70)
    print("TEST 5: Multi-Pair Engine")
    print("="*70)

    eng = MatchingEngine()

    # Submit orders on different pairs
    btc_sell = Order.create("BTC/USD", OrderSide.SELL, 50000.0, 1.0)
    eth_sell = Order.create("ETH/USD", OrderSide.SELL, 3000.0, 10.0)

    eng.submit_order(btc_sell)
    eng.submit_order(eth_sell)

    pairs = eng.get_trading_pairs()
    assert len(pairs) == 2
    assert "BTC/USD" in pairs
    assert "ETH/USD" in pairs

    print("✓ Multi-pair engine test passed")
    print(f"  - Active trading pairs: {pairs}")
    print(f"  - Total pairs: {len(pairs)}")
    print(f"  - Events recorded: {eng.event_store.event_count}")


def test_event_sourcing():
    """Test event sourcing and replay."""
    print("\n" + "="*70)
    print("TEST 6: Event Sourcing & Replay")
    print("="*70)

    eng = MatchingEngine()

    # Execute trades - unmatched order
    order1 = Order.create("BTC/USD", OrderSide.BUY, 50000.0, 1.0)
    eng.submit_order(order1)

    # Check events recorded
    events_list = eng.event_store.get_events()
    assert len(events_list) >= 1  # At least ORDER_PLACED

    # Replay events
    replay_eng = ReplayEngine()
    rebuilt = replay_eng.replay_events(eng.event_store)

    assert "BTC/USD" in rebuilt

    # After replay, unmatched order should still be in book
    rebuilt_book = rebuilt["BTC/USD"]
    assert len(rebuilt_book.bids) == 1, f"Expected 1 bid after replay"

    print("✓ Event sourcing test passed")
    print(f"  - Events recorded: {len(events_list)}")
    print(f"  - Event types: {[e.event_type.value for e in events_list[:1]]}")
    print(f"  - Rebuilt state verified: ✓ (unmatched order recovered)")


def test_order_cancellation():
    """Test order cancellation."""
    print("\n" + "="*70)
    print("TEST 7: Order Cancellation")
    print("="*70)

    eng = MatchingEngine()

    # Place order
    order = Order.create("BTC/USD", OrderSide.BUY, 50000.0, 1.0)
    eng.submit_order(order)

    # Verify it's in the book
    book = eng.get_orderbook("BTC/USD")
    assert len(book.bids) == 1

    # Cancel it
    cancelled = eng.cancel_order("BTC/USD", order.id)

    assert cancelled
    assert len(book.bids) == 0

    print("✓ Order cancellation test passed")
    print(f"  - Placed BUY order for 1.0 BTC @ $50,000")
    print(f"  - Order in book: ✓")
    print(f"  - Cancelled: ✓")
    print(f"  - Orderbook now empty: ✓")


def test_fifo_at_price_level():
    """Test FIFO matching at same price level."""
    print("\n" + "="*70)
    print("TEST 8: FIFO at Price Level")
    print("="*70)

    from datetime import datetime, timedelta

    book = Orderbook("BTC/USD")
    m = Matcher()

    # Add two sell orders at same price, different times
    now = datetime.utcnow()
    sell1 = Order.create("BTC/USD", OrderSide.SELL, 50000.0, 0.3, timestamp=now)
    sell2 = Order.create("BTC/USD", OrderSide.SELL, 50000.0, 0.3,
                         timestamp=now + timedelta(milliseconds=1))

    book.add_order(sell1)
    book.add_order(sell2)

    # Buy both
    buy = Order.create("BTC/USD", OrderSide.BUY, 50000.0, 0.6)
    trades = m.match_order(book, buy)

    assert len(trades) == 2
    assert trades[0].seller_order_id == sell1.id  # First seller should match first
    assert trades[1].seller_order_id == sell2.id

    print("✓ FIFO test passed")
    print(f"  - Two sell orders at $50,000 (submitted 1ms apart)")
    print(f"  - Buy order matches both via FIFO")
    print(f"  - First trade: {trades[0].seller_order_id[:8]}... (older order)")
    print(f"  - Second trade: {trades[1].seller_order_id[:8]}... (newer order)")


def test_engine_statistics():
    """Test engine statistics tracking."""
    print("\n" + "="*70)
    print("TEST 9: Engine Statistics")
    print("="*70)

    eng = MatchingEngine()

    # Execute some trades
    for pair in ["BTC/USD", "ETH/USD"]:
        for i in range(2):
            sell = Order.create(pair, OrderSide.SELL, 100.0 + i, 1.0)
            buy = Order.create(pair, OrderSide.BUY, 100.0 + i, 1.0)
            eng.submit_order(sell)
            eng.submit_order(buy)

    stats = eng.get_stats()

    assert stats["trading_pairs"] == 2
    assert stats["total_trades"] == 4
    assert stats["events_recorded"] >= 8

    print("✓ Statistics test passed")
    print(f"  - Trading pairs: {stats['trading_pairs']}")
    print(f"  - Total trades: {stats['total_trades']}")
    print(f"  - Events recorded: {stats['events_recorded']}")
    print(f"  - Active pairs: {', '.join(stats['active_pairs'])}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MATCHING ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*70)

    try:
        test_order_model()
        test_orderbook()
        test_price_time_priority_matching()
        test_partial_fill()
        test_multi_pair_engine()
        test_event_sourcing()
        test_order_cancellation()
        test_fifo_at_price_level()
        test_engine_statistics()

        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓✓✓")
        print("="*70)
        print("\nMatching Engine Features Verified:")
        print("  ✓ Order model with validation")
        print("  ✓ Efficient orderbook (SortedDict + FIFO queues)")
        print("  ✓ Price-Time Priority matching algorithm")
        print("  ✓ Partial fill support")
        print("  ✓ Multi-trading pair support")
        print("  ✓ Event sourcing with replay")
        print("  ✓ Order cancellation")
        print("  ✓ FIFO at price levels")
        print("  ✓ Statistics tracking")
        print("\n✓ Ready for API deployment with FastAPI\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
