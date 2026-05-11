"""Risk analyst agent - focuses on position sizing and portfolio impact."""

from dataclasses import dataclass
from typing import Optional
from memecoin_trader.backend.agents.base import (
    TradingAgent,
    Analysis,
    Critique,
    AgentVote,
    AgentContext
)
from memecoin_trader.backend.core.config import settings


class RiskAnalystAgent(TradingAgent):
    """Agent that focuses on risk management and position sizing."""
    
    name = "risk_analyst"
    perspective = "Risk and position sizing"
    description = "Evaluates portfolio impact, position sizing, and worst-case scenarios"
    
    def __init__(self):
        super().__init__()
        self.max_position = settings.capital_protection.MAX_POSITION_SIZE
        self.daily_loss_limit = settings.capital_protection.DAILY_LOSS_LIMIT
        self.drawdown_limit = settings.capital_protection.DRAWDOWN_PAUSE
    
    async def analyze(self, token_data: dict, context: dict) -> Analysis:
        """Analyze risk and position sizing."""
        findings = []
        warnings = []
        concerns = []
        evidence = {}
        
        # Get portfolio state from context
        portfolio_value = context.get("portfolio_value", 0)
        daily_pnl_pct = context.get("daily_pnl_pct", 0)
        drawdown = context.get("drawdown", 0)
        open_positions = context.get("open_positions", [])
        
        # Check daily loss limit
        if daily_pnl_pct < -self.daily_loss_limit:
            concerns.append(f"Daily loss {abs(daily_pnl_pct):.1%} exceeds limit")
            evidence["daily_loss"] = daily_pnl_pct
        elif daily_pnl_pct < -self.daily_loss_limit * 0.5:
            warnings.append(f"Daily loss at {abs(daily_pnl_pct):.1%}")
            evidence["daily_loss"] = daily_pnl_pct
        
        # Check drawdown
        if drawdown > self.drawdown_limit:
            concerns.append(f"Drawdown {drawdown:.1%} exceeds limit")
            evidence["drawdown"] = drawdown
        elif drawdown > self.drawdown_limit * 0.5:
            warnings.append(f"Drawdown at {drawdown:.1%}")
            evidence["drawdown"] = drawdown
        
        # Check position sizing
        proposed_size = context.get("proposed_position_size", 0)
        if portfolio_value > 0:
            proposed_pct = proposed_size / portfolio_value
            
            if proposed_pct > self.max_position:
                concerns.append(
                    f"Position {proposed_pct:.1%} exceeds max {self.max_position:.1%}"
                )
                evidence["proposed_position"] = proposed_pct
            elif proposed_pct > self.max_position * 0.8:
                warnings.append(
                    f"Position {proposed_pct:.1%} near max"
                )
                evidence["proposed_position"] = proposed_pct
        
        # Check correlation with existing positions
        if open_positions:
            # Check if already have similar exposure
            similar = sum(1 for p in open_positions if p.get("token") == token_data.get("address"))
            if similar > 0:
                concerns.append(f"Already have position in this token")
                evidence["duplicate_exposure"] = True
        
        # Calculate confidence based on risk
        if concerns:
            recommendation = AgentVote.SKIP
            confidence = 0.90
            reasoning = f"Risk concerns: {len(concerns)} blocking issue(s)"
        elif warnings:
            recommendation = AgentVote.UNCERTAIN
            confidence = 0.55
            reasoning = f"Risk warnings present: {warnings[0]}"
        else:
            recommendation = AgentVote.BUY
            confidence = 0.80
            reasoning = "Risk parameters acceptable"
        
        return Analysis(
            agent_name=self.name,
            perspective=self.perspective,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            key_findings=findings,
            warnings=warnings,
            concerns=concerns,
            supporting_evidence=evidence
        )
    
    async def critique(self, other_analyses: list[Analysis]) -> list[Critique]:
        """Critique other agents' analyses."""
        critiques = []
        
        for analysis in other_analyses:
            critique_text = ""
            agreement = True
            suggestions = []
            counter = {}
            
            # Cross-check with momentum
            if analysis.agent_name == "momentum":
                if analysis.recommendation == AgentVote.BUY:
                    evidence = analysis.supporting_evidence
                    volume = evidence.get("volume_spike", 0)
                    
                    # Very high volume may indicate unsustainable entry
                    if volume > 15:
                        critique_text = f"Volume spike {volume}x may be too high for entry"
                        agreement = False
                        suggestions.append("Wait for stabilization")
            
            # Check skeptic
            elif analysis.agent_name == "skeptic":
                if analysis.recommendation == AgentVote.SKIP:
                    concerns = analysis.concerns
                    if len(concerns) == 1:
                        critique_text = "Single concern - consider sizing down instead of skip"
                        agreement = True
            
            critique = Critique(
                from_agent=self.name,
                to_agent=analysis.agent_name,
                critique_text=critique_text,
                agreement=agreement,
                suggested_changes=suggestions,
                counter_evidence=counter
            )
            critiques.append(critique)
        
        return critiques
    
    async def refine(
        self,
        critiques: list[Critique],
        original_analysis: Analysis
    ) -> Analysis:
        """Refine analysis based on critiques."""
        new_warnings = original_analysis.warnings.copy()
        
        # Reduce position if needed
        evidence = dict(original_analysis.supporting_evidence)
        
        for critique in critiques:
            if not critique.to_agent == self.name and not critique.agreement:
                if "volume" in critique.critique_text.lower():
                    new_warnings.append("High volume - consider reduced position")
        
        # Lower confidence if warnings
        confidence = original_analysis.confidence
        if len(new_warnings) > len(original_analysis.warnings):
            confidence = max(0.5, confidence - 0.1)
        
        return Analysis(
            agent_name=self.name,
            perspective=self.perspective,
            recommendation=original_analysis.recommendation,
            confidence=confidence,
            reasoning=original_analysis.reasoning,
            key_findings=original_analysis.key_findings,
            warnings=new_warnings,
            concerns=original_analysis.concerns,
            supporting_evidence=evidence
        )