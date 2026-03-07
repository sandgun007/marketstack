"""FastAPI REST gateway for the matching engine."""
import asyncio
from typing import List, Optional, Dict, Set
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import sys
import os
import json

# Add matching engine directory to path
matching_engine_path = os.path.join(
    os.path.dirname(__file__),
    '../..',
    'core/matching-engine'
)
sys.path.insert(0, matching_engine_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import from matching engine
try:
    from models import Order, OrderSide
    from engine import MatchingEngine
except ImportError:
    # Fallback for when running from different directory
    from core.matching_engine.models import Order, OrderSide
    from core.matching_engine.engine import MatchingEngine

# Initialize app
app = FastAPI(
    title="Matching Engine API",
    description="High-performance crypto exchange matching engine",
    version="1.0.0",
)

# ============================================================================
# CORS Configuration - Allow requests from all origins (for dashboard)
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify: ["http://localhost:3000", "http://localhost:8080", "file://"])
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Global engine instance
engine = MatchingEngine()

# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time market data."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, trading_pair: str):
        """Register a new WebSocket connection."""
        await websocket.accept()
        if trading_pair not in self.active_connections:
            self.active_connections[trading_pair] = set()
        self.active_connections[trading_pair].add(websocket)

    def disconnect(self, websocket: WebSocket, trading_pair: str):
        """Remove a WebSocket connection."""
        if trading_pair in self.active_connections:
            self.active_connections[trading_pair].discard(websocket)
            if not self.active_connections[trading_pair]:
                del self.active_connections[trading_pair]

    async def broadcast(self, trading_pair: str, message: dict):
        """Send message to all connected clients for a trading pair."""
        if trading_pair not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[trading_pair]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, trading_pair)

manager = ConnectionManager()

# ============================================================================
# Request/Response Models
# ============================================================================


class OrderRequest(BaseModel):
    """Request to submit an order."""
    trading_pair: str = Field(..., example="BTC/USD")
    side: str = Field(..., example="BUY")
    price: float = Field(..., example=50000.0)
    quantity: float = Field(..., example=1.0)


class TradeResponse(BaseModel):
    """Trade execution response."""
    id: str
    trading_pair: str
    buyer_order_id: str
    seller_order_id: str
    quantity: float
    price: float
    timestamp: str


class OrderSubmissionResponse(BaseModel):
    """Response from order submission."""
    order_id: str
    trading_pair: str
    quantity: float
    remaining_quantity: float
    status: str
    trades_executed: List[TradeResponse]


class OrderbookLevel(BaseModel):
    """Single price level in orderbook."""
    price: float
    quantity: float


class OrderbookSnapshot(BaseModel):
    """Current orderbook snapshot."""
    trading_pair: str
    best_bid: Optional[float]
    best_ask: Optional[float]
    bids: List[OrderbookLevel]
    asks: List[OrderbookLevel]


class EngineStats(BaseModel):
    """Engine statistics."""
    trading_pairs: int
    total_trades: int
    events_recorded: int
    active_pairs: List[str]


class TickerData(BaseModel):
    """Market ticker data."""
    trading_pair: str
    best_bid: float
    best_ask: float
    last_trade_price: Optional[float] = None
    spread: float
    spread_percent: float


class HistoryCandle(BaseModel):
    """OHLCV candle for price history."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class OrderHistory(BaseModel):
    """Historical order information."""
    order_id: str
    trading_pair: str
    side: str
    price: float
    quantity: float
    remaining_quantity: float
    status: str
    created_at: str
    filled_at: Optional[str] = None


class OrdersResponse(BaseModel):
    """Response for order history query."""
    orders: List[OrderHistory]
    total: int
    limit: int
    offset: int


# ============================================================================
# Endpoints
# ============================================================================


@app.post("/orders", response_model=OrderSubmissionResponse)
async def submit_order(req: OrderRequest) -> OrderSubmissionResponse:
    """
    Submit an order for matching.

    Returns:
    - order_id: Unique identifier for the order
    - status: Current order status (ACTIVE, PARTIALLY_FILLED, or FILLED)
    - trades_executed: List of trades immediately executed
    """
    try:
        # Parse order side
        side = OrderSide.BUY if req.side.upper() == "BUY" else OrderSide.SELL

        # Create order
        order = Order.create(
            trading_pair=req.trading_pair,
            side=side,
            price=req.price,
            quantity=req.quantity,
        )

        # Submit to engine (runs in thread-safe manner)
        trades = engine.submit_order(order)

        # Format trades
        trades_response = [
            TradeResponse(
                id=t.id,
                trading_pair=t.trading_pair,
                buyer_order_id=t.buyer_order_id,
                seller_order_id=t.seller_order_id,
                quantity=t.quantity,
                price=t.price,
                timestamp=t.timestamp.isoformat(),
            )
            for t in trades
        ]

        # Broadcast market update to WebSocket clients
        asyncio.create_task(
            _broadcast_market_update(req.trading_pair, trades_response)
        )

        return OrderSubmissionResponse(
            order_id=order.id,
            trading_pair=order.trading_pair,
            quantity=order.quantity,
            remaining_quantity=order.remaining_quantity,
            status=order.status.value,
            trades_executed=trades_response,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str, trading_pair: str) -> Dict:
    """
    Cancel an existing order.

    Parameters:
    - order_id: Order ID to cancel
    - trading_pair: Trading pair (e.g., BTC/USD)

    Returns:
    - success: Whether cancellation succeeded
    - message: Status message
    """
    try:
        success = engine.cancel_order(trading_pair, order_id)
        if success:
            return {"success": True, "message": f"Order {order_id} cancelled"}
        else:
            raise HTTPException(
                status_code=404, detail=f"Order {order_id} not found"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/orders/{order_id}")
async def update_order(order_id: str, trading_pair: str, new_quantity: float) -> Dict:
    """
    Update order quantity (cancel + re-add).

    Parameters:
    - order_id: Order ID to update
    - trading_pair: Trading pair
    - new_quantity: New order quantity
    """
    try:
        success = engine.update_order_quantity(trading_pair, order_id, new_quantity)
        if success:
            return {
                "success": True,
                "message": f"Order {order_id} updated to {new_quantity}",
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Order {order_id} not found"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orderbook/{trading_pair:path}", response_model=OrderbookSnapshot)
async def get_orderbook(trading_pair: str, depth: int = 20) -> OrderbookSnapshot:
    """
    Get current orderbook snapshot.

    Parameters:
    - trading_pair: Trading pair (e.g., BTC/USD)
    - depth: Number of levels to return (default 20)

    Returns:
    - Best bid/ask and top N price levels
    """
    try:
        snapshot = engine.get_orderbook_snapshot(trading_pair, depth)
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"No orderbook for {trading_pair}",
            )

        bids = [OrderbookLevel(price=b["price"], quantity=b["quantity"]) for b in snapshot["bids"]]
        asks = [OrderbookLevel(price=a["price"], quantity=a["quantity"]) for a in snapshot["asks"]]

        return OrderbookSnapshot(
            trading_pair=trading_pair,
            best_bid=snapshot["best_bid"],
            best_ask=snapshot["best_ask"],
            bids=bids,
            asks=asks,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trades/{trading_pair:path}")
async def get_trades(trading_pair: str, limit: int = 100) -> List[TradeResponse]:
    """
    Get recent trades for a trading pair.

    Parameters:
    - trading_pair: Trading pair
    - limit: Number of recent trades to return
    """
    try:
        trades = engine.get_trades(trading_pair)
        trades = trades[-limit:] if limit > 0 else trades

        return [
            TradeResponse(
                id=t.id,
                trading_pair=t.trading_pair,
                buyer_order_id=t.buyer_order_id,
                seller_order_id=t.seller_order_id,
                quantity=t.quantity,
                price=t.price,
                timestamp=t.timestamp.isoformat(),
            )
            for t in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=EngineStats)
async def get_stats() -> EngineStats:
    """Get engine statistics."""
    stats = engine.get_stats()
    return EngineStats(**stats)


@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "engine_stats": engine.get_stats(),
    }


@app.get("/market/ticker/{trading_pair:path}", response_model=TickerData)
async def get_ticker(trading_pair: str) -> TickerData:
    """Get market ticker data for a trading pair."""
    try:
        snapshot = engine.get_orderbook_snapshot(trading_pair, 1)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"No data for {trading_pair}")

        best_bid = snapshot.get("best_bid", 0)
        best_ask = snapshot.get("best_ask", 0)
        spread = best_ask - best_bid if best_bid and best_ask else 0
        spread_percent = (spread / best_bid * 100) if best_bid else 0

        # Get last trade price
        trades = engine.get_trades(trading_pair)
        last_trade_price = trades[-1].price if trades else None

        return TickerData(
            trading_pair=trading_pair,
            best_bid=best_bid or 0,
            best_ask=best_ask or 0,
            last_trade_price=last_trade_price,
            spread=round(spread, 2),
            spread_percent=round(spread_percent, 4),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/history/{trading_pair:path}", response_model=List[HistoryCandle])
async def get_price_history(trading_pair: str, limit: int = 100) -> List[HistoryCandle]:
    """Get OHLCV price history for a trading pair."""
    try:
        trades = engine.get_trades(trading_pair)
        if not trades:
            return []

        # Group trades by hour for OHLCV
        from datetime import timedelta
        from collections import defaultdict

        candles_dict = defaultdict(lambda: {"high": 0, "low": float('inf'), "volume": 0, "open": None, "close": None})

        for trade in trades[-limit:]:  # Get last N trades
            hour_key = trade.timestamp.replace(minute=0, second=0, microsecond=0).isoformat()

            if candles_dict[hour_key]["open"] is None:
                candles_dict[hour_key]["open"] = trade.price

            candles_dict[hour_key]["close"] = trade.price
            candles_dict[hour_key]["high"] = max(candles_dict[hour_key]["high"], trade.price)
            candles_dict[hour_key]["low"] = min(candles_dict[hour_key]["low"], trade.price)
            candles_dict[hour_key]["volume"] += trade.quantity

        # Convert to candles
        candles = [
            HistoryCandle(
                timestamp=timestamp,
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
                volume=data["volume"],
            )
            for timestamp, data in sorted(candles_dict.items())
        ]

        return candles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders", response_model=OrdersResponse)
async def get_orders_history(
    limit: int = 50,
    offset: int = 0,
    status: str = "all",
) -> OrdersResponse:
    """Get historical orders with optional filtering."""
    try:
        # Get all trades to build order history
        all_trades = []
        order_map = {}

        # Iterate through all trading pairs
        for pair in engine.get_trading_pairs():
            trades = engine.get_trades(pair)
            for trade in trades:
                all_trades.append((trade, pair))

        # Group trades by order (use buyer and seller order IDs)
        orders_dict = {}

        # Note: This is a simplified implementation
        # In production, you'd want to store order history directly in the engine
        # For now, we return recent trades as "orders"
        recent_trades = sorted(all_trades, key=lambda x: x[0].timestamp, reverse=True)

        orders_list = []
        for trade, pair in recent_trades[:limit + offset]:
            # Create synthetic order entry from trade
            order_entry = OrderHistory(
                order_id=trade.buyer_order_id,
                trading_pair=pair,
                side="BUY",
                price=trade.price,
                quantity=trade.quantity,
                remaining_quantity=0,
                status="FILLED",
                created_at=trade.timestamp.isoformat(),
                filled_at=trade.timestamp.isoformat(),
            )
            orders_list.append(order_entry)

        # Apply offset
        paginated_orders = orders_list[offset : offset + limit]

        return OrdersResponse(
            orders=paginated_orders,
            total=len(orders_list),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoints - Real-time Market Data
# ============================================================================


async def _broadcast_market_update(trading_pair: str, trades: List[TradeResponse]):
    """Broadcast market update to all connected WebSocket clients."""
    try:
        snapshot = engine.get_orderbook_snapshot(trading_pair, 20)
        if not snapshot:
            return

        bids = [{"price": b["price"], "quantity": b["quantity"]} for b in snapshot["bids"]]
        asks = [{"price": a["price"], "quantity": a["quantity"]} for a in snapshot["asks"]]

        message = {
            "type": "market_update",
            "trading_pair": trading_pair,
            "timestamp": datetime.utcnow().isoformat(),
            "best_bid": snapshot["best_bid"],
            "best_ask": snapshot["best_ask"],
            "bids": bids,
            "asks": asks,
            "recent_trades": [
                {
                    "id": t.id,
                    "quantity": t.quantity,
                    "price": t.price,
                    "timestamp": t.timestamp,
                }
                for t in trades
            ],
        }

        await manager.broadcast(trading_pair, message)
    except Exception as e:
        print(f"Error broadcasting market update: {e}")


@app.websocket("/ws/market/{trading_pair:path}")
async def websocket_market_endpoint(websocket: WebSocket, trading_pair: str):
    """
    WebSocket endpoint for real-time market data.

    Clients connect to: ws://localhost:8000/ws/market/BTC/USD
    Receives streaming orderbook and trade updates as they happen.
    """
    await manager.connect(websocket, trading_pair)

    # Send initial snapshot
    try:
        snapshot = engine.get_orderbook_snapshot(trading_pair, 20)
        if snapshot:
            bids = [{"price": b["price"], "quantity": b["quantity"]} for b in snapshot["bids"]]
            asks = [{"price": a["price"], "quantity": a["quantity"]} for a in snapshot["asks"]]

            await websocket.send_json({
                "type": "snapshot",
                "trading_pair": trading_pair,
                "timestamp": datetime.utcnow().isoformat(),
                "best_bid": snapshot["best_bid"],
                "best_ask": snapshot["best_ask"],
                "bids": bids,
                "asks": asks,
            })
    except Exception as e:
        print(f"Error sending initial snapshot: {e}")

    try:
        while True:
            # Keep connection alive - client can send ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, trading_pair)
        print(f"Client disconnected from {trading_pair}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, trading_pair)


# ============================================================================
# Startup/Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize engine on startup."""
    print("✓ Matching engine initialized")
    print("✓ Ready to accept orders")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("✓ Matching engine shutting down")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("Starting Matching Engine API Server...")
    print("Docs available at: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
