#!/usr/bin/env python3
"""
Test client for the Matching Engine API Gateway
Makes requests to a running gateway server
"""
import requests
import json
import time
import sys

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*70)
    print("TEST: Health Check")
    print("="*70)
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        if resp.status_code == 200:
            print("✅ Server is healthy")
            data = resp.json()
            print(f"   Status: {data['status']}")
            print(f"   Trading pairs: {data['engine_stats']['trading_pairs']}")
        else:
            print(f"❌ Unexpected status: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://localhost:8000")
        print("   Make sure gateway is running: python3 run_gateway.py")
        sys.exit(1)

def test_submit_sell_order():
    """Test submitting a sell order"""
    print("\n" + "="*70)
    print("TEST: Submit Sell Order")
    print("="*70)

    order_data = {
        "trading_pair": "BTC/USD",
        "side": "SELL",
        "price": 50000.0,
        "quantity": 1.0
    }

    resp = requests.post(f"{BASE_URL}/orders", json=order_data)

    if resp.status_code == 200:
        data = resp.json()
        print("✅ Sell order submitted")
        print(f"   Order ID: {data['order_id'][:8]}...")
        print(f"   Status: {data['status']}")
        print(f"   Remaining: {data['remaining_quantity']} BTC")
        return data['order_id']
    else:
        print(f"❌ Failed: {resp.status_code}")
        print(f"   {resp.text}")
        return None

def test_submit_buy_order():
    """Test submitting a matching buy order"""
    print("\n" + "="*70)
    print("TEST: Submit Matching Buy Order")
    print("="*70)

    order_data = {
        "trading_pair": "BTC/USD",
        "side": "BUY",
        "price": 50000.0,
        "quantity": 1.0
    }

    resp = requests.post(f"{BASE_URL}/orders", json=order_data)

    if resp.status_code == 200:
        data = resp.json()
        print("✅ Buy order submitted")
        print(f"   Order ID: {data['order_id'][:8]}...")
        print(f"   Status: {data['status']}")
        print(f"   Remaining: {data['remaining_quantity']} BTC")

        # Check if trades were executed
        if data['trades_executed']:
            print(f"\n   ✅ TRADES EXECUTED: {len(data['trades_executed'])}")
            for i, trade in enumerate(data['trades_executed'], 1):
                print(f"   Trade {i}: {trade['quantity']} BTC @ ${trade['price']}")
        else:
            print(f"\n   No trades (order in book)")

        return data['order_id']
    else:
        print(f"❌ Failed: {resp.status_code}")
        print(f"   {resp.text}")
        return None

def test_query_orderbook():
    """Test querying the orderbook"""
    print("\n" + "="*70)
    print("TEST: Query Orderbook")
    print("="*70)

    resp = requests.get(f"{BASE_URL}/orderbook/BTC/USD?depth=5")

    if resp.status_code == 200:
        data = resp.json()
        print("✅ Got orderbook snapshot")
        print(f"   Pair: {data['trading_pair']}")
        print(f"   Best bid: ${data['best_bid']}")
        print(f"   Best ask: ${data['best_ask']}")
        print(f"   Bid levels: {len(data['bids'])}")
        print(f"   Ask levels: {len(data['asks'])}")

        if data['bids']:
            print(f"\n   TOP BIDS:")
            for bid in data['bids'][:3]:
                print(f"   ${bid['price']}: {bid['quantity']} BTC")

        if data['asks']:
            print(f"\n   TOP ASKS:")
            for ask in data['asks'][:3]:
                print(f"   ${ask['price']}: {ask['quantity']} BTC")
    else:
        print(f"❌ Failed: {resp.status_code}")

def test_get_stats():
    """Test getting engine statistics"""
    print("\n" + "="*70)
    print("TEST: Engine Statistics")
    print("="*70)

    resp = requests.get(f"{BASE_URL}/stats")

    if resp.status_code == 200:
        data = resp.json()
        print("✅ Engine statistics")
        print(f"   Trading pairs: {data['trading_pairs']}")
        print(f"   Total trades: {data['total_trades']}")
        print(f"   Events recorded: {data['events_recorded']}")
        print(f"   Active pairs: {', '.join(data['active_pairs'])}")
    else:
        print(f"❌ Failed: {resp.status_code}")

def test_get_trades():
    """Test getting trade history"""
    print("\n" + "="*70)
    print("TEST: Trade History")
    print("="*70)

    resp = requests.get(f"{BASE_URL}/trades/BTC/USD?limit=10")

    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Got {len(data)} recent trades")

        if data:
            print("\n   Recent trades:")
            for i, trade in enumerate(data[:3], 1):
                print(f"   {i}. {trade['quantity']} BTC @ ${trade['price']}")
    else:
        print(f"❌ Failed: {resp.status_code}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MATCHING ENGINE API TEST CLIENT")
    print("="*70)

    try:
        # Test health
        test_health()

        # Test orders
        sell_id = test_submit_sell_order()
        if sell_id:
            buy_id = test_submit_buy_order()

        # Test queries
        test_query_orderbook()
        test_get_stats()
        test_get_trades()

        print("\n" + "="*70)
        print("✅ TESTS COMPLETED")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
