"""Event store - in-memory event storage with optional file persistence."""
from collections import deque
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
import json

if TYPE_CHECKING:
    from events import Event, EventType
else:
    try:
        from .events import Event, EventType
    except (ImportError, ValueError):
        from events import Event, EventType


class EventStore:
    """In-memory event store with optional file backup."""

    def __init__(self, backup_file: Optional[str] = None):
        self.events: deque = deque()
        self.backup_file = backup_file
        self._event_count = 0

    def append(self, event: Event) -> None:
        """Add event to store."""
        self.events.append(event)
        self._event_count += 1

    def get_events(self) -> List[Event]:
        """Get all events."""
        return list(self.events)

    def get_events_for_pair(self, trading_pair: str) -> List[Event]:
        """Get all events for a trading pair."""
        return [e for e in self.events if e.trading_pair == trading_pair]

    def get_events_for_order(self, order_id: str) -> List[Event]:
        """Get all events for a specific order."""
        return [e for e in self.events if e.order_id == order_id]

    def get_events_since(self, timestamp: datetime) -> List[Event]:
        """Get all events since a timestamp."""
        return [e for e in self.events if e.timestamp >= timestamp]

    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get most recent N events."""
        if limit <= 0:
            return list(self.events)
        return list(self.events)[-limit:]

    def snapshot(self) -> dict:
        """Create a snapshot of current state."""
        return {
            "event_count": self.event_count,
            "timestamp": datetime.utcnow().isoformat(),
            "events": [self._event_to_dict(e) for e in self.events],
        }

    def save_snapshot(self, filepath: str) -> None:
        """Save snapshot to file."""
        snap = self.snapshot()
        with open(filepath, "w") as f:
            json.dump(snap, f, indent=2, default=str)

    @staticmethod
    def _event_to_dict(event: Event) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            "id": event.id,
            "event_type": event.event_type.value,
            "trading_pair": event.trading_pair,
            "timestamp": event.timestamp.isoformat(),
            "order_id": event.order_id,
            "details": event.details,
        }

    @property
    def event_count(self) -> int:
        """Get total number of events."""
        return self._event_count

    def __len__(self) -> int:
        return len(self.events)

    def __repr__(self) -> str:
        return f"EventStore(events={len(self.events)})"
