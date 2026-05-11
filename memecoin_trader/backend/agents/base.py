"""Base class for trading agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class AgentVote(Enum):
    """Possible agent votes."""
    BUY = "BUY"
    SKIP = "SKIP"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class Analysis:
    """Analysis output from an agent."""
    agent_name: str
    perspective: str
    recommendation: AgentVote
    confidence: float  # 0.0 to 1.0
    reasoning: str
    key_findings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    supporting_evidence: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "perspective": self.perspective,
            "recommendation": self.recommendation.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "key_findings": self.key_findings,
            "warnings": self.warnings,
            "concerns": self.concerns,
            "supporting_evidence": self.supporting_evidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Critique:
    """Critique of another agent's analysis."""
    from_agent: str
    to_agent: str
    critique_text: str
    agreement: bool  # Does this agent agree with the other?
    suggested_changes: list[str] = field(default_factory=list)
    counter_evidence: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "critique_text": self.critique_text,
            "agreement": self.agreement,
            "suggested_changes": self.suggested_changes,
            "counter_evidence": self.counter_evidence,
            "timestamp": self.timestamp.isoformat()
        }


class TradingAgent(ABC):
    """Base class for trading agents."""
    
    name: str = "base_agent"
    perspective: str = "General analysis"
    description: str = "Base trading agent"
    
    def __init__(self):
        self._enabled = True
    
    @abstractmethod
    async def analyze(self, token_data: dict, context: dict) -> Analysis:
        """Analyze a token.
        
        Args:
            token_data: Token information
            context: Additional context (market data, etc.)
            
        Returns:
            Analysis with recommendation and reasoning
        """
        pass
    
    @abstractmethod
    async def critique(self, other_analyses: list[Analysis]) -> Critique:
        """Critique other agents' analyses.
        
        Args:
            other_analyses: List of other agents' analyses
            
        Returns:
            Critique of each analysis
        """
        pass
    
    @abstractmethod
    async def refine(
        self, 
        critiques: list[Critique], 
        original_analysis: Analysis
    ) -> Analysis:
        """Refine analysis based on critiques.
        
        Args:
            critiques: List of critiques from other agents
            original_analysis: Original analysis to refine
            
        Returns:
            Refined analysis
        """
        pass
    
    @property
    def is_enabled(self) -> bool:
        """Check if agent is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable this agent."""
        self._enabled = True
    
    def disable(self):
        """Disable this agent."""
        self._enabled = False


# Type alias for agent context
AgentContext = dict