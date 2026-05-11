"""Trade recorder for learning loop."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from pathlib import Path
import json

from memecoin_trader.backend.core.logging import trade_logger


@dataclass
class TradeRecord:
    """Record of a trade decision."""
    token: str
    token_name: str = ""
    decision: str = ""  # "BUY", "SKIP", or "NOT_TRADED"
    signals: list[str] = field(default_factory=list)
    filter_results: dict = field(default_factory=dict)
    agent_votes: dict = field(default_factory=dict)
    confidence: float = 0.0
    position_size: float = 0.0
    
    # Outcome (filled later)
    outcome: Optional[float] = None  # PnL percentage
    realized_pnl: float = 0.0
    holding_time_hours: float = 0.0
    exit_reason: str = ""
    post_mortem: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "token_name": self.token_name,
            "decision": self.decision,
            "signals": self.signals,
            "filter_results": self.filter_results,
            "agent_votes": self.agent_votes,
            "confidence": self.confidence,
            "position_size": self.position_size,
            "outcome": self.outcome,
            "realized_pnl": self.realized_pnl,
            "holding_time_hours": self.holding_time_hours,
            "exit_reason": self.exit_reason,
            "post_mortem": self.post_mortem,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TradeRecord":
        record = cls(
            token=data.get("token", ""),
            token_name=data.get("token_name", ""),
            decision=data.get("decision", ""),
            signals=data.get("signals", []),
            filter_results=data.get("filter_results", {}),
            agent_votes=data.get("agent_votes", {}),
            confidence=data.get("confidence", 0.0),
            position_size=data.get("position_size", 0.0),
            outcome=data.get("outcome"),
            realized_pnl=data.get("realized_pnl", 0.0),
            holding_time_hours=data.get("holding_time_hours", 0.0),
            exit_reason=data.get("exit_reason", ""),
            post_mortem=data.get("post_mortem", "")
        )
        
        if "created_at" in data:
            record.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            record.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return record


class TradeRecorder:
    """Records trades for learning."""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("./data/trades")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, record: TradeRecord):
        """Save a trade record."""
        # Use token address as filename (first 16 chars)
        filename = record.token[:16] + ".json"
        path = self.data_dir / filename
        
        with open(path, "w") as f:
            json.dump(record.to_dict(), f, indent=2)
        
        trade_logger.log_signal(
            record.token,
            record.decision,
            record.confidence,
            signals=record.signals,
            agent_votes=record.agent_votes
        )
    
    def load(self, token: str) -> Optional[TradeRecord]:
        """Load a trade record."""
        filename = token[:16] + ".json"
        path = self.data_dir / filename
        
        if not path.exists():
            return None
        
        with open(path) as f:
            data = json.load(f)
        
        return TradeRecord.from_dict(data)
    
    def update_outcome(
        self,
        token: str,
        outcome: float,
        realized_pnl: float,
        holding_time_hours: float,
        exit_reason: str,
        post_mortem: str = ""
    ):
        """Update trade outcome."""
        record = self.load(token)
        
        if record:
            record.outcome = outcome
            record.realized_pnl = realized_pnl
            record.holding_time_hours = holding_time_hours
            record.exit_reason = exit_reason
            record.post_mortem = post_mortem
            record.updated_at = datetime.utcnow()
            self.save(record)
    
    def get_all_records(self) -> list[TradeRecord]:
        """Get all trade records."""
        records = []
        
        for path in self.data_dir.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
            records.append(TradeRecord.from_dict(data))
        
        return sorted(records, key=lambda r: r.created_at, reverse=True)
    
    def get_records_with_outcome(self) -> list[TradeRecord]:
        """Get trades with known outcomes."""
        return [r for r in self.get_all_records() if r.outcome is not None]
    
    def get_stats(self) -> dict:
        """Get trading statistics."""
        trades = self.get_records_with_outcome()
        
        if not trades:
            return {
                "total_trades": 0,
                "profitable_trades": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0
            }
        
        profitable = [t for t in trades if t.realized_pnl > 0]
        
        return {
            "total_trades": len(trades),
            "profitable_trades": len(profitable),
            "win_rate": len(profitable) / len(trades),
            "avg_pnl": sum(t.realized_pnl for t in trades) / len(trades),
            "best_trade": max(t.realized_pnl for t in trades),
            "worst_trade": min(t.realized_pnl for t in trades)
        }


# Singleton recorder
_recorder: Optional[TradeRecorder] = None


def get_recorder() -> TradeRecorder:
    """Get the global recorder instance."""
    global _recorder
    if _recorder is None:
        _recorder = TradeRecorder()
    return _recorder