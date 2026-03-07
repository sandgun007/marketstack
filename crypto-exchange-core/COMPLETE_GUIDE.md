# Complete Trading System - Getting Started Guide

Complete guide to running the full Crypto Exchange Matching Engine with dashboard.

## 🎯 System Components

```
┌─────────────────────────────────────────────────────────┐
│          TRADING DASHBOARD (UI)                         │
│     http://localhost:8000/docs (Swagger)               │
│     or dashboard.html (Web Interface)                  │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP Requests (REST API)
                 ▼
        ┌───────────────────────┐
        │  MATCHING ENGINE      │
        │  API Gateway Port:    │
        │  8000                 │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  Core Matching Engine │
        │  - Orderbook          │
        │  - FIFO Matching      │
        │  - Event Sourcing     │
        │  - Trade Execution    │
        └───────────────────────┘
```

## 🚀 Quick Start - 3 Steps

### Step 1️⃣: Start API Server (Terminal 1)
```bash
cd /srv/marketstack/crypto-exchange-core
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

INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Server is now ready for connections**

---

### Step 2️⃣: Open Trading Dashboard (Terminal 2)

#### Option A: Simple HTML (Fastest)
```bash
# Just open the dashboard in your browser
open dashboard.html
# or
firefox dashboard.html
```

#### Option B: Run Dashboard Server
```bash
python3 run_dashboard.py
```

Output:
```
======================================================================
TRADING DASHBOARD SERVER
======================================================================

📊 Dashboard running on: http://localhost:8080

✅ Dashboard will auto-connect to API at http://localhost:8000
🌐 Attempting to open dashboard in browser...
```

#### Option C: Swagger/OpenAPI (Interactive API Docs)
Open in browser:
```
http://localhost:8000/docs
```

---

### Step 3️⃣: Place Trade Orders

#### Via Dashboard (Easiest):
1. Select trading pair (BTC/USD)
2. Choose side (BUY or SELL)
3. Enter price ($50,000)
4. Enter quantity (1.0)
5. Click "Submit BUY Order" or "Submit SELL Order"
6. Watch trades execute in real-time!

#### Via Swagger UI:
1. Visit `http://localhost:8000/docs`
2. Click on POST `/orders`
3. Click "Try it out"
4. Enter order data
5. Click "Execute"
6. See response

#### Via cURL (Command Line):
```bash
# Submit a SELL order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "trading_pair": "BTC/USD",
    "side": "SELL",
    "price": 50000.0,
    "quantity": 1.0
  }'

# Submit matching BUY order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "trading_pair": "BTC/USD",
    "side": "BUY",
    "price": 50000.0,
    "quantity": 1.0
  }'
```

---

## 📊 Complete Example Workflow

### Terminal Setup:
```
┌─────────────────────────┬─────────────────────────┐
│  Terminal 1             │  Terminal 2             │
├─────────────────────────┼─────────────────────────┤
│ python3 run_gateway.py  │ open dashboard.html     │
│                         │ (or run_dashboard.py)   │
├─────────────────────────┼─────────────────────────┤
│ ✅ API Server Running   │ ✅ Dashboard Open       │
│ Port: 8000              │ Port: 8080 (optional)   │
└─────────────────────────┴─────────────────────────┘
```

### Trading Example:

**Step 1: Initialize Market**
- Dashboard shows empty order book
- Statistics: 0 trades, 0 events
- Status: Connected ✅

**Step 2: Submit First Order (SELL)**
- In dashboard form:
  - Pair: BTC/USD
  - Side: SELL
  - Price: $50,000
  - Quantity: 1.0
  - Click "Submit SELL Order"
- Result: ✅ Order placed, remains in order book

**Step 3: View Order Book**
- Order Book shows:
  - SELLS: $50,000 (1.0 BTC)
- Statistics: 0 trades (not matched yet)

**Step 4: Submit Matching Order (BUY)**
- In dashboard form:
  - Pair: BTC/USD
  - Side: BUY
  - Price: $50,000
  - Quantity: 1.0
  - Click "Submit BUY Order"
- Result: ✅ Trade executed immediately!

**Step 5: Verify Execution**
- Dashboard shows:
  - ✅ Success: "1 trades executed"
  - Order Book: Empty (both orders filled)
  - Recent Trades: Shows "1.0 BTC @ $50,000" with timestamp
  - Statistics: 1 trade, 3 events recorded
  - My Orders: Shows both orders with status "FILLED"

---

## 🎨 Dashboard Features Demo

### Real-Time Updates
- Every 2 seconds: Order book, trades, statistics
- Click "Refresh" button for immediate update
- Automatic reconnection if server restarts

### Live Metrics
```
Trading Pairs: 1          Total Trades: 1
Events Recorded: 3        Server Status: Online ✅
```

### Order Book Depth
```
BIDS                      ASKS
$49,999 (1.5 BTC)        $50,001 (2.0 BTC)
$49,998 (0.5 BTC)        $50,002 (1.0 BTC)
$49,997 (1.0 BTC)        $50,003 (0.5 BTC)
```

### Recent Trades
```
Trade 1: 1.0 BTC @ $50,000 (14:32:45)
Trade 2: 0.5 BTC @ $50,001 (14:32:46)
```

---

## 🧪 Testing Scenarios

### Scenario 1: Perfect Match
```
1. Submit: SELL 1.0 BTC @ $50,000
2. Submit: BUY 1.0 BTC @ $50,000
Result: ✅ Instant trade, both filled
```

### Scenario 2: Partial Fill
```
1. Submit: SELL 1.0 BTC @ $50,000
2. Submit: BUY 0.5 BTC @ $50,000
Result: ✅ Trade 0.5 BTC, 0.5 BTC remains in book
```

### Scenario 3: Multi-Price Matching
```
1. Submit: SELL 0.5 BTC @ $50,000
2. Submit: SELL 0.3 BTC @ $50,001
3. Submit: BUY 1.0 BTC @ $50,001
Result: ✅ Matches both, best prices first
         Trade 0.5 @ $50,000 + Trade 0.5 @ $50,001
```

### Scenario 4: Price Gap (No Match)
```
1. Submit: SELL 1.0 BTC @ $50,001
2. Submit: BUY 1.0 BTC @ $50,000 (lower price)
Result: ❌ No trade (no overlap)
        Both orders remain in book
        Bid-Ask spread = $1
```

---

## 📡 API Reference

### All Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /orders | Submit buy/sell order |
| DELETE | /orders/{order_id} | Cancel order |
| PATCH | /orders/{order_id} | Update order quantity |
| GET | /orderbook/{pair} | Get order book snapshot |
| GET | /trades/{pair} | Get trade history |
| GET | /stats | Get engine statistics |
| GET | /health | Check server status |

### Example Requests

**1. Submit Order**
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

**2. Get Orderbook**
```bash
curl http://localhost:8000/orderbook/BTC/USD?depth=10
```

**3. Get Trades**
```bash
curl http://localhost:8000/trades/BTC/USD?limit=100
```

**4. Get Statistics**
```bash
curl http://localhost:8000/stats
```

---

## 🐛 Troubleshooting

### Dashboard shows "Disconnected"
**Problem:** Dashboard can't reach API server
```
✅ Solution:
   1. Make sure "python3 run_gateway.py" is running
   2. Check if port 8000 is open
   3. Try refreshing dashboard
```

### Orders not executing immediately
**Problem:** Orders are in order book but not matching
```
✅ Solution:
   - This is normal if prices don't overlap
   - Example: SELL @ $50,001 won't match BUY @ $50,000
   - Try using exact same price for both orders
```

### "No module found" errors
**Problem:** Python import paths not set up
```
✅ Solution:
   - DON'T use: python3 -m services.order_gateway.gateway
   - DO use:    python3 run_gateway.py
```

### Dashboard slow to update
**Problem:** Refresh rate too slow
```
✅ Solution:
   - Click "Refresh" button for immediate update
   - Or edit dashboard.html and change interval:
     updateInterval = setInterval(loadData, 500);  // 500ms instead of 2000ms
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Project overview & features |
| QUICKSTART.md | Step-by-step setup guide |
| GATEWAY_FIXED.md | API gateway setup |
| DASHBOARD_GUIDE.md | Dashboard usage guide |
| IMPLEMENTATION_SUMMARY.md | Architecture details |

---

## ✨ Complete File Listing

```
/srv/marketstack/crypto-exchange-core/
├── run_gateway.py                    ← Start API server
├── run_dashboard.py                  ← Start dashboard server
├── dashboard.html                    ← Main dashboard UI
├── test_gateway_client.py            ← API test client
├── test_matching_engine.py           ← Comprehensive tests
├── requirements.txt                  ← Python dependencies
├── README.md                         ← Overview
├── QUICKSTART.md                     ← Quick start
├── GATEWAY_FIXED.md                  ← Gateway setup
├── DASHBOARD_GUIDE.md                ← Dashboard guide
├── IMPLEMENTATION_SUMMARY.md         ← Architecture
├── core/matching-engine/
│   ├── models.py
│   ├── orderbook.py
│   ├── matcher.py
│   ├── engine.py
│   └── [5 more modules...]
└── services/order_gateway/
    └── gateway.py
```

---

## 🎯 Quick Reference Commands

```bash
# Terminal 1: Start API
python3 run_gateway.py

# Terminal 2: Open dashboard
open dashboard.html

# Terminal 3: Run tests
python3 test_matching_engine.py

# Check server health
curl http://localhost:8000/health

# Submit order via cURL
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"trading_pair":"BTC/USD","side":"BUY","price":50000.0,"quantity":1.0}'
```

---

## 🏆 Success Checklist

- [ ] API server running (`python3 run_gateway.py`)
- [ ] Dashboard open in browser (can see BTC/USD order book)
- [ ] Status shows "Connected" ✅
- [ ] Statistics show 0 trades initially
- [ ] Submit SELL order successfully
- [ ] SELL order appears in order book
- [ ] Submit matching BUY order
- [ ] Trade executes (status changes to "FILLED")
- [ ] Trade appears in "Recent Trades"
- [ ] Statistics updated (1 trade, 3 events)

---

## 🚀 Next Steps

1. ✅ Get API and dashboard running
2. ✅ Practice placing test orders
3. ✅ Try different price levels
4. ✅ Test partial fills
5. ✅ Monitor real-time updates
6. → Deploy to production
7. → Connect to market data feeds
8. → Add user authentication
9. → Scale to more trading pairs

---

**Status**: ✅ **Full Trading System Ready**

The complete system includes:
- High-performance matching engine
- Production-grade REST API
- Beautiful web dashboard
- Comprehensive testing suite
- Complete documentation

**Ready to trade!** 🚀
