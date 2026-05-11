"""Trading agents for memecoin analysis."""

from memecoin_trader.backend.agents.base import (
    TradingAgent,
    Analysis,
    Critique,
    AgentVote,
    AgentContext
)
from memecoin_trader.backend.agents.skeptic import SkepticAgent
from memecoin_trader.backend.agents.momentum import MomentumAgent
from memecoin_trader.backend.agents.wallet_tracker import WalletTrackerAgent
from memecoin_trader.backend.agents.risk_analyst import RiskAnalystAgent
from memecoin_trader.backend.agents.debate import (
    DebateProtocol,
    DebateResult,
    DebateRound,
    create_debate_protocol
)

__all__ = [
    "TradingAgent",
    "Analysis",
    "Critique",
    "AgentVote",
    "AgentContext",
    "SkepticAgent",
    "MomentumAgent",
    "WalletTrackerAgent",
    "RiskAnalystAgent",
    "DebateProtocol",
    "DebateResult",
    "DebateRound",
    "create_debate_protocol",
]