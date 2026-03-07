# QUICK START - Running the Matching Engine API

## 📦 Prerequisites

Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

(This installs: sortedcontainers, fastapi, uvicorn, pytest)

## 🧪 Step 1: Run Tests

First, verify everything is working:

```bash
python3 test_matching_engine.py
```

Expected output:
```
✓ All modules imported successfully
[9 comprehensive tests run...]
ALL TESTS PASSED ✓✓✓
```

## 🚀 Step 2: Start the Gateway Server

In terminal #1, start the API server:

```bash
python3 run_gateway.py
```

Expected output:
```
======================================================================
MATCHING ENGINE - REST API GATEWAY
======================================================================

📡 Starting server...
   API URL: http://localhost:8000
   Docs:    http://localhost:8000/docs
   ReDoc:   http://localhost:8000/redoc

✅ Ready to accept orders

INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 📡 Step 3: Test the API

In terminal #2, use either:

### Option A: Test Client Script
```bash
python3 test_gateway_client.py
```

This will:
- Check server health
- Submit a SELL order
- Submit a matching BUY order
- Query the orderbook
- Get trade history
- Display engine statistics

Expected output:
```
======================================================================
MATCHING ENGINE API TEST CLIENT
======================================================================

TEST: Health Check
✅ Server is healthy

TEST: Submit Sell Order
✅ Sell order submitted

TEST: Submit Matching Buy Order
✅ Buy order submitted
   ✅ TRADES EXECUTED: 1
   Trade 1: 1.0 BTC @ $50000.0

TEST: Query Orderbook
✅ Got orderbook snapshot

TEST: Engine Statistics
✅ Engine statistics

TEST: Trade History
✅ Got 1 recent trades
```

### Option B: Manual cURL Requests

**1. Health Check:**
```bash
curl http://localhost:8000/health
```

**2. Submit Order:**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "trading_pair": "BTC/USD",
    "side": "BUY",
    "price": 50000.0,
    "quantity": 1.0
  }'
```

**3. Query Orderbook:**
```bash
curl http://localhost:8000/orderbook/BTC/USD
```

**4. Get Trades:**
```bash
curl http://localhost:8000/trades/BTC/USD
```

**5. Engine Stats:**
```bash
curl http://localhost:8000/stats
```

**6. Cancel Order:**
```bash
curl -X DELETE "http://localhost:8000/orders/{order_id}?trading_pair=BTC/USD"
```

### Option C: Interactive Swagger UI

Open your browser and visit:
```
http://localhost:8000/docs
```

This opens the Swagger UI where you can:
- Try out all endpoints interactively
- See request/response schemas
- Read endpoint documentation

## 🎯 API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /orders | Submit new order |
| DELETE | /orders/{order_id} | Cancel order |
| PATCH | /orders/{order_id} | Update order quantity |
| GET | /orderbook/{pair} | Get orderbook snapshot |
| GET | /trades/{pair} | Get recent trades |
| GET | /stats | Get engine statistics |
| GET | /health | Health check |

## 📊 Example Workflow

### 1. Submit a SELL order for 1 BTC @ $50,000:
```json
POST /orders
{
  "trading_pair": "BTC/USD",
  "side": "SELL",
  "price": 50000.0,
  "quantity": 1.0
}
```

Response:
```json
{
  "order_id": "abc123...",
  "trading_pair": "BTC/USD",
  "quantity": 1.0,
  "remaining_quantity": 1.0,
  "status": "ACTIVE",
  "trades_executed": []
}
```

### 2. Submit a matching BUY order for 1 BTC @ $50,000:
```json
POST /orders
{
  "trading_pair": "BTC/USD",
  "side": "BUY",
  "price": 50000.0,
  "quantity": 1.0
}
```

Response:
```json
{
  "order_id": "def456...",
  "trading_pair": "BTC/USD",
  "quantity": 1.0,
  "remaining_quantity": 0.0,
  "status": "FILLED",
  "trades_executed": [
    {
      "id": "trade123...",
      "trading_pair": "BTC/USD",
      "buyer_order_id": "def456...",
      "seller_order_id": "abc123...",
      "quantity": 1.0,
      "price": 50000.0,
      "timestamp": "2026-03-07T..."
    }
  ]
}
```

### 3. Query the orderbook:
```
GET /orderbook/BTC/USD
```

Response:
```json
{
  "trading_pair": "BTC/USD",
  "best_bid": null,
  "best_ask": null,
  "bids": [],
  "asks": []
}
```

Both orders are fully matched and filled!

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'core.matching_engine'"

**Solution:** Use the provided `run_gateway.py` script which sets up paths correctly:
```bash
python3 run_gateway.py
```

NOT:
```bash
python3 -m services.order_gateway.gateway  # ❌ Don't use this
```

### "Connection refused" when running test_gateway_client.py

**Solution:** Make sure the gateway server is running in another terminal:
```bash
python3 run_gateway.py
```

### "ModuleNotFoundError: No module named 'fastapi'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install fastapi uvicorn sortedcontainers pytest
```

## 📝 Next Steps

1. ✅ Verify tests pass
2. ✅ Start gateway server
3. ✅ Test with client script
4. ✅ Explore Swagger UI
5. → Deploy to production
6. → Connect market data feeds
7. → Add settlement services

## 📞 Support

For more information, see:
- `README.md` - Project overview
- `IMPLEMENTATION_SUMMARY.md` - Architecture details
- `test_matching_engine.py` - Feature examples
- `http://localhost:8000/docs` - API documentation

---

**Status**: ✅ Ready to use! The matching engine is fully operational.
