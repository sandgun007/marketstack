# Trading Dashboard - User Guide

A beautiful web dashboard for the Crypto Exchange Matching Engine with real-time order book, trade execution, and statistics.

## 🚀 Quick Start

### Method 1: Open Directly (Easiest)

Simply open the HTML file in your browser:
```bash
# Assumes API server is running on http://localhost:8000
open dashboard.html
# or
firefox dashboard.html
# or
google-chrome dashboard.html
```

**Note**: Make sure the matching engine API server is running first:
```bash
python3 run_gateway.py
```

### Method 2: Serve with Python (Optional)

If you're on a different machine or need to serve over network:

```bash
# Simple HTTP server (Python 3)
python3 -m http.server 8001

# Then open in browser: http://localhost:8001/dashboard.html
```

Or use any web server:
```bash
# Node.js
npx http-server .

# Ruby
ruby -run -ehttpd . -p8001

# PHP
php -S localhost:8001
```

## 📊 Dashboard Features

### 1. **Server Status** (Top Right)
- 🟢 **Connected** - API is reachable
- 🔴 **Disconnected** - API is offline
- Auto-connects every time you interact

### 2. **Order Form** (Left Panel)
Place buy/sell orders with:
- **Trading Pair** - Select from BTC/USD, ETH/USD, XRP/USD
- **Side** - Choose BUY or SELL
- **Price** - Limit order price in USD
- **Quantity** - Order size in crypto

**Tips:**
- For test trades, use round numbers (e.g., 1.0 BTC)
- Prices update automatically as you type
- Button changes color based on BUY/SELL

### 3. **Engine Statistics** (Top Middle)
Real-time metrics:
- **Trading Pairs** - Active markets
- **Total Trades** - All executed trades
- **Events Recorded** - Full audit trail
- **Server Status** - Online/Offline indicator

### 4. **Market Info** (Top Right)
- List of active trading pairs
- Quick market status
- "Load Market Data" button to refresh

### 5. **Order Book** (Bottom Left)
Shows live order book depth:
- **💰 BIDS (Green)** - Buy orders sorted by price
- **💸 ASKS (Red)** - Sell orders sorted by price
- Click "Refresh" to manually update

Example:
```
BIDS                 ASKS
$49,999 (1.5 BTC)   $50,001 (2.0 BTC)
$49,998 (0.5 BTC)   $50,002 (1.0 BTC)
```

### 6. **Recent Activity** (Bottom Right)

#### **Recent Trades Tab** 📖
Shows matched trades with:
- Execution price
- Quantity traded
- Exact timestamp

#### **My Orders Tab** 📋
Shows your submitted orders:
- Side (BUY/SELL)
- Price and quantity
- Current status (ACTIVE, FILLED, etc.)

## 💡 Usage Examples

### Example 1: Simple Trade Matching

1. **Submit a SELL order:**
   - Pair: BTC/USD
   - Side: SELL
   - Price: $50,000
   - Quantity: 1.0
   - Click "Submit SELL Order"

2. **Submit matching BUY order:**
   - Pair: BTC/USD
   - Side: BUY
   - Price: $50,000
   - Quantity: 1.0
   - Click "Submit BUY Order"

3. **Result:**
   - ✅ Success message appears
   - Trade immediately executes
   - Both orders disappear from order book
   - Trade appears in "Recent Trades"

### Example 2: Partial Fill

1. **Submit a SELL order for 1.0 BTC @ $50,000**
2. **Submit a BUY order for 0.5 BTC @ $50,000**
3. **Result:**
   - Trade executes for 0.5 BTC
   - SELL order still has 0.5 BTC remaining in order book
   - Trade shows in Recent Trades
   - My Orders shows remaining SELL order as PARTIAL

### Example 3: Multi-Price Trading

1. **Submit SELL orders at different prices:**
   - 1.0 BTC @ $50,001
   - 1.0 BTC @ $50,002
   - 1.0 BTC @ $50,003

2. **Submit BUY order for 2.5 BTC @ $50,003**

3. **Result:**
   - Matches with best prices first:
     - 1.0 BTC @ $50,001 ✅
     - 1.0 BTC @ $50,002 ✅
     - 0.5 BTC @ $50,003 ✅
   - 3 trades recorded
   - 0.5 BTC @ $50,003 remains in order book

## 🎨 Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  📈 Crypto Trading Dashboard    [● Connected] [↻ Refresh] │
└─────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┐
│              │              │              │
│   Order      │  Statistics  │  Market      │
│   Form       │  (Metrics)   │  Info        │
│              │              │              │
├──────────────┴──────────────┴──────────────┤
│                                            │
│  ┌──────────────┐  ┌──────────────┐      │
│  │   BIDS/ASKS  │  │  Recent      │      │
│  │   (Order     │  │  Activity    │      │
│  │   Book)      │  │  (Trades &   │      │
│  │              │  │  Orders)     │      │
│  └──────────────┘  └──────────────┘      │
│                                            │
└────────────────────────────────────────────┘
```

## 🔄 Auto-Refresh

The dashboard automatically refreshes every **2 seconds**:
- Order book updates
- New trades appear
- Statistics refresh
- Server status checked

Click **↻ Refresh** button to manually refresh immediately.

## ⚙️ Customization

### Change API URL
Open dashboard.html in text editor and modify:
```javascript
const API_URL = 'http://localhost:8000';  // Change this
```

### Add More Trading Pairs
Find this section and add options:
```html
<select id="tradingPair" required>
    <option value="BTC/USD">BTC/USD</option>
    <option value="ETH/USD">ETH/USD</option>
    <!-- Add more here -->
    <option value="ADA/USD">ADA/USD</option>
</select>
```

### Change Refresh Interval
Modify this line (time in milliseconds):
```javascript
updateInterval = setInterval(loadData, 2000); // Change 2000 to desired ms
```

## 🐛 Troubleshooting

### "Disconnected" Status?
- ✅ Make sure `python3 run_gateway.py` is running
- ✅ Check if API is on `http://localhost:8000`
- ✅ No firewall blocking port 8000
- ✅ If different port, edit `API_URL` in dashboard.html

### Orders Not Appearing?
- ✅ Check that orders were submitted (success message shown)
- ✅ Try clicking Refresh button
- ✅ Check browser console for errors (F12 → Console)
- ✅ Make sure matching engine core is working

### Dashboard Not Loading?
- ✅ Try opening in a different browser
- ✅ Clear browser cache (Ctrl+Shift+Delete)
- ✅ Check browser developer tools (F12) for errors
- ✅ Make sure file path is correct

### Trades Executing Unexpectedly?
- ✅ Perfect! That means Price-Time Priority matching is working
- ✅ Overlapping bid-ask prices = instant trade execution
- ✅ Check "Recent Trades" tab to see all executions

## 📱 Mobile Compatibility

Dashboard is responsive and works on:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Tablets (iPad, Android tablets)
- ✅ Mobile phones (reduced layout)

Layouts adapt automatically for smaller screens.

## 🎯 Features Summary

| Feature | Status |
|---------|--------|
| Real-time order book | ✅ |
| Order submission (BUY/SELL) | ✅ |
| Trade execution display | ✅ |
| Engine statistics | ✅ |
| Auto-refresh (2s) | ✅ |
| Manual refresh | ✅ |
| Connected/Disconnected status | ✅ |
| Multi-pair support | ✅ |
| Trade history | ✅ |
| Order status tracking | ✅ |
| Responsive design | ✅ |
| Color-coded bids/asks | ✅ |
| Success/Error messages | ✅ |

## 📚 Integration with Backend

The dashboard connects to these API endpoints:
- `GET /health` - Server status
- `POST /orders` - Submit orders
- `GET /orderbook/{pair}` - Get order book
- `GET /trades/{pair}` - Get trade history
- `GET /stats` - Get engine statistics

All communication is asynchronous (non-blocking).

## 🚀 Next Steps

1. ✅ Open `dashboard.html` in browser
2. ✅ Make sure API server is running
3. ✅ Submit some test orders
4. ✅ Watch trades execute in real-time
5. ✅ Check statistics and trade history

---

**Tip:** For best experience, keep the API server running in one terminal and dashboard open in browser. The dashboard will automatically reconnect if server restarts!

**Questions?** Check the browser console (F12) for any error messages that might help troubleshoot.
