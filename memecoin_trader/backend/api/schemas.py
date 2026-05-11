"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TokenDataRequest(BaseModel):
    """Request for token analysis."""
    address: str
    name: str = ""


class TokenDataResponse(BaseModel):
    """Token data response."""
    address: str
    name: str = ""
    price: float = 0.0
    price_change_24h: float = 0.0
    liquidity_usd: float = 0.0
    volume_24h: float = 0.0
    top10_concentration: float = 0.0
    holder_count: int = 0
    can_buy: bool = True
    can_sell: bool = True
    mint_authority: str = ""


class FilterResultResponse(BaseModel):
    """Filter evaluation result."""
    filter_name: str
    passed: bool
    confidence: float
    reason: str
    warnings: List[str] = []


class AnalysisResponse(BaseModel):
    """Agent analysis result."""
    agent_name: str
    perspective: str
    recommendation: str
    confidence: float
    reasoning: str
    key_findings: List[str] = []
    warnings: List[str] = []
    concerns: List[str] = []


class DebateResponse(BaseModel):
    """Debate result response."""
    token: str
    success: bool
    consensus_reached: bool
    consensus_score: float
    votes: dict
    reason: str
    analyses: List[AnalysisResponse] = []


class SignalResponse(BaseModel):
    """Trading signal response."""
    token_address: str
    action: str
    position_size_sol: float
    entry_conditions: List[str] = []
    target_exit: float = 0.0
    stop_loss: float = 0.0
    confidence: float = 0.0
    agent_votes: dict = {}
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PositionResponse(BaseModel):
    """Position response."""
    token: str
    token_name: str
    size_sol: float
    entry_price: float
    current_price: float = 0.0
    pnl_pct: float = 0.0
    pnl_sol: float = 0.0
    opened_at: datetime
    status: str = "open"


class PerformanceResponse(BaseModel):
    """Performance stats response."""
    total_trades: int
    profitable_trades: int
    win_rate: float
    avg_pnl: float
    best_trade: float
    worst_trade: float
    filters: List[dict] = []


class GuardCheckResponse(BaseModel):
    """Guard check response."""
    action: str
    guard_name: str
    message: str
    details: dict = {}


class OverrideRequest(BaseModel):
    """Manual override request."""
    token: str = ""
    action: str  # "force_buy", "force_skip", "pause", "resume"
    reason: str = ""
    filter_adjustments: dict = {}


class ExecuteSignalRequest(BaseModel):
    """Execute signal request."""
    token: str
    position_size_sol: float
    slippage: float = 0.01


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"