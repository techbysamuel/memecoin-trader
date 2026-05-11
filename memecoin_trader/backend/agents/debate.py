"""Multi-agent debate protocol."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from memecoin_trader.backend.agents.base import TradingAgent, Analysis, Critique, AgentVote
from memecoin_trader.backend.core.config import settings
from memecoin_trader.backend.core.exceptions import NoConsensusError


@dataclass
class DebateRound:
    """A single round of debate."""
    round_number: int
    analyses: list[Analysis] = field(default_factory=list)
    critiques: list[Critique] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class DebateResult:
    """Final result of a debate."""
    token: str
    success: bool
    consensus_reached: bool
    consensus_score: float  # 0.0 to 1.0
    final_analyses: list[Analysis] = field(default_factory=list)
    votes: dict[str, str] = field(default_factory=dict)  # agent -> vote
    rounds: list[DebateRound] = field(default_factory=list)
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "success": self.success,
            "consensus_reached": self.consensus_reached,
            "consensus_score": self.consensus_score,
            "votes": self.votes,
            "reason": self.reason,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "analyses": [a.to_dict() for a in r.analyses],
                    "critiques": [c.to_dict() for c in r.critiques]
                }
                for r in self.rounds
            ],
            "timestamp": self.timestamp.isoformat()
        }


class DebateProtocol:
    """Multi-agent debate protocol."""
    
    def __init__(
        self,
        agents: list[TradingAgent],
        rounds: int = None,
        consensus_threshold: float = None
    ):
        self.agents = agents
        self.rounds = rounds or settings.agents.debate_rounds
        self.consensus_threshold = consensus_threshold or settings.agents.consensus_threshold
        self.min_agents = settings.agents.min_agents_for_trade
    
    async def run_debate(
        self,
        token: str,
        token_data: dict,
        context: dict
    ) -> DebateResult:
        """Run full debate protocol.
        
        Args:
            token: Token address
            token_data: Token information
            context: Additional context
            
        Returns:
            DebateResult with final consensus
        """
        debate_rounds = []
        
        # Round 0: Initial analysis
        analyses = []
        for agent in self.agents:
            if agent.is_enabled:
                analysis = await agent.analyze(token_data, context)
                analyses.append(analysis)
        
        debate_rounds.append(DebateRound(round_number=0, analyses=list(analyses)))
        
        # Subsequent rounds: critique and refine
        for round_num in range(1, self.rounds + 1):
            # Collect critiques from all agents
            all_critiques = []
            for agent in self.agents:
                if agent.is_enabled:
                    critiques = await agent.critique(analyses)
                    all_critiques.extend(critiques)
            
            debate_rounds.append(
                DebateRound(
                    round_number=round_num,
                    analyses=list(analyses),
                    critiques=list(all_critiques)
                )
            )
            
            # Refine analyses based on critiques
            refined_analyses = []
            for agent in self.agents:
                if agent.is_enabled:
                    # Find this agent's analysis from previous round
                    prev_analysis = next(
                        (a for a in analyses if a.agent_name == agent.name),
                        analyses[0]
                    )
                    refined = await agent.refine(all_critiques, prev_analysis)
                    refined_analyses.append(refined)
            
            analyses = refined_analyses
        
        # Calculate final vote
        votes = {a.recommendation.value for a in analyses}
        vote_counts = {}
        for a in analyses:
            vote_counts[a.recommendation.value] = vote_counts.get(a.recommendation.value, 0) + 1
        
        # Calculate consensus
        buy_votes = vote_counts.get(AgentVote.BUY.value, 0)
        total_agents = len([a for a in self.agents if a.is_enabled])
        consensus_score = buy_votes / total_agents if total_agents > 0 else 0
        
        # Check if consensus reached
        consensus_reached = (
            consensus_score >= self.consensus_threshold and
            buy_votes >= self.min_agents
        )
        
        if consensus_reached:
            return DebateResult(
                token=token,
                success=True,
               consensus_reached=True,
                consensus_score=consensus_score,
                final_analyses=list(analyses),
                votes={a.agent_name: a.recommendation.value for a in analyses},
                rounds=debate_rounds,
                reason=f"Consensus reached: {buy_votes}/{total_agents} agents voted BUY"
            )
        else:
            return DebateResult(
                token=token,
                success=False,
                consensus_reached=False,
                consensus_score=consensus_score,
                final_analyses=list(analyses),
                votes={a.agent_name: a.recommendation.value for a in analyses},
                rounds=debate_rounds,
                reason=f"No consensus: {buy_votes}/{total_agents} agents voted BUY"
            )
    
    def get_agent_by_name(self, name: str) -> Optional[TradingAgent]:
        """Get agent by name."""
        return next((a for a in self.agents if a.name == name), None)


def create_debate_protocol() -> DebateProtocol:
    """Create debate protocol with all agents."""
    from memecoin_trader.backend.agents.skeptic import SkepticAgent
    from memecoin_trader.backend.agents.momentum import MomentumAgent
    from memecoin_trader.backend.agents.wallet_tracker import WalletTrackerAgent
    from memecoin_trader.backend.agents.risk_analyst import RiskAnalystAgent
    
    agents = [
        SkepticAgent(),
        MomentumAgent(),
        WalletTrackerAgent(),
        RiskAnalystAgent()
    ]
    
    return DebateProtocol(agents=agents)