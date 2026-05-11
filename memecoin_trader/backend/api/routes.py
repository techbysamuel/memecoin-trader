"""API routes for memecoin trading system."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from memecoin_trader.backend.api.schemas import (
    TokenDataRequest,
    TokenDataResponse,
    FilterResultResponse,
    AnalysisResponse,
    DebateResponse,
    SignalResponse,
    PositionResponse,
    PerformanceResponse,
    OverrideRequest,
    ExecuteSignalRequest,
    HealthResponse
)
from memecoin_trader.backend.filters import FilterPipeline
from memecoin_trader.backend.agents import create_debate_protocol
from memecoin_trader.backend.learning import get_recorder, get_analyzer
from memecoin_trader.backend.execution import get_guards


router = APIRouter()
filters = FilterPipeline()
debate_protocol = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@router.get("/tokens/candidates")
async def get_token_candidates(
    min_liquidity: float = 30000,
    min_volume: float = 10000
):
    """Get filtered token candidates."""
    # Would fetch from data sources in production
    return {
        "tokens": [],
        "count": 0,
        "filters_applied": ["liquidity", "holder_concentration", "rug_detection", "volume"]
    }


@router.post("/tokens/analyze")
async def analyze_token(request: TokenDataRequest):
    """Analyze a token through the filter pipeline."""
    # Would fetch token data in production
    token_data = {
        "address": request.address,
        "name": request.name,
        "liquidity_usd": 0,
        "volume_24h": 0,
        "top10_concentration": 0,
        "holders": []
    }
    
    # Run filters
    results = await filters.evaluate(token_data)
    
    return {
        "token": request.address,
        "filter_results": [FilterResultResponse(
            filter_name="test",
            passed=r.passed,
            confidence=r.confidence,
            reason=r.reason,
            warnings=r.warnings
        ).to_dict() for r in results],
        "overall_result": "PASSED" if all(r.passed for r in results) else "FAILED"
    }


@router.get("/tokens/{address}/analysis")
async def get_token_analysis(address: str):
    """Get full agent analysis for a token."""
    global debate_protocol
    
    if debate_protocol is None:
        debate_protocol = create_debate_protocol()
    
    # Would fetch token data in production
    token_data = {
        "address": address,
        "liquidity_usd": 50000,
        "volume_24h": 100000,
        "top10_concentration": 0.3
    }
    
    context = {
        "portfolio_value": 10.0,
        "daily_pnl_pct": 0.0,
        "drawdown": 0.0,
        "open_positions": []
    }
    
    result = await debate_protocol.run_debate(
        token=address,
        token_data=token_data,
        context=context
    )
    
    return result.to_dict()


@router.get("/agents/debates")
async def get_active_debates():
    """Get active debates."""
    return {"debates": []}


@router.post("/signals/execute")
async def execute_signal(request: ExecuteSignalRequest):
    """Execute a trading signal (autonomous mode)."""
    guards = get_guards()
    
    # For now, just verify guards
    can_trade, reason = guards.can_trade(
        portfolio_value=10.0,
        proposed_position=request.position_size_sol,
        daily_pnl_pct=0.0,
        drawdown=0.0,
        confidence=0.8
    )
    
    return {
        "success": can_trade,
        "reason": reason,
        "token": request.token,
        "position_size": request.position_size_sol
    }


@router.get("/positions")
async def get_positions():
    """Get open positions."""
    return {"positions": []}


@router.get("/performance")
async def get_performance():
    """Get performance stats."""
    analyzer = get_analyzer()
    summary = analyzer.get_performance_summary(days=30)
    return summary


@router.post("/settings/override")
async def add_override(request: OverrideRequest):
    """Add manual override."""
    return {
        "success": True,
        "action": request.action,
        "reason": request.reason
    }


@router.get("/learning/recommendations")
async def get_learning_recommendations():
    """Get filter recommendations."""
    analyzer = get_analyzer()
    recommendations = analyzer.get_recommendations(days=30)
    return {"recommendations": recommendations}


def create_router() -> APIRouter:
    """Create and configure router."""
    return router