"""Momentum agent - focuses on volume and price flow."""

from dataclasses import dataclass
from typing import Optional
from memecoin_trader.backend.agents.base import (
    TradingAgent,
    Analysis,
    Critique,
    AgentVote,
    AgentContext
)


class MomentumAgent(TradingAgent):
    """Agent that focuses on volume and price momentum."""
    
    name = "momentum"
    perspective = "Volume and price flow analysis"
    description = "Analyzes momentum indicators, breakout patterns, and sustained buying pressure"
    
    async def analyze(self, token_data: dict, context: dict) -> Analysis:
        """Analyze token for momentum patterns."""
        findings = []
        warnings = []
        concerns = []
        evidence = {}
        
        # Check volume spike
        volume_24h = token_data.get("volume_24h", 0)
        baseline = token_data.get("baseline_volume", 0)
        volume_spike = volume_24h / baseline if baseline > 0 else 0
        
        if volume_spike > 5:
            findings.append(f"Strong volume spike: {volume_spike:.1f}x")
            evidence["volume_spike"] = volume_spike
        elif volume_spike > 2:
            findings.append(f"Moderate volume spike: {volume_spike:.1f}x")
            evidence["volume_spike"] = volume_spike
        
        # Check price action
        price_change = token_data.get("price_change_24h", 0)
        if price_change > 0.5:  # 50% up
            findings.append(f"Strong price action: +{price_change:.1%}")
            evidence["price_change_24h"] = price_change
        elif price_change > 0.1:
            findings.append(f"Positive price action: +{price_change:.1%}")
            evidence["price_change_24h"] = price_change
        
        # Check for sustained buying (not just pump)
        buy_sell_ratio = token_data.get("buy_sell_ratio", 1.0)
        if buy_sell_ratio > 2:
            findings.append(f"Buy/sell ratio: {buy_sell_ratio:.1f}x")
            evidence["buy_sell_ratio"] = buy_sell_ratio
        
        # Check holder growth
        new_holders = token_data.get("new_holders_24h", 0)
        if new_holders > 50:
            findings.append(f"New holders: {new_holders}")
            evidence["new_holders"] = new_holders
        elif new_holders > 0:
            warnings.append(f"Limited new holders: {new_holders}")
            evidence["new_holders"] = new_holders
        
        # Check multiple DEX presence
        dex_count = token_data.get("dex_count", 0)
        if dex_count > 1:
            findings.append(f"Multiple DEX support: {dex_count}")
            evidence["dex_count"] = dex_count
        else:
            warnings.append("Single DEX - lower liquidity diversity")
            evidence["dex_count"] = dex_count
        
        # Determine recommendation
        score = len(findings)
        
        if score >= 3 and volume_spike > 3:
            recommendation = AgentVote.BUY
            confidence = 0.85
            reasoning = f"Strong momentum: {', '.join(findings[:2])}"
        elif score >= 2 and volume_spike > 2:
            recommendation = AgentVote.BUY
            confidence = 0.70
            reasoning = f"Moderate momentum with {findings[0] if findings else 'volume'}"
        elif warnings and not findings:
            recommendation = AgentVote.UNCERTAIN
            confidence = 0.50
            reasonings = f"Weak momentum signals: {warnings[0]}"
        else:
            recommendation = AgentVote.SKIP
            confidence = 0.65
            reasoning = "Insufficient momentum for trade"
        
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
            
            # Challenge skeptic to be less conservative
            if analysis.agent_name == "skeptic":
                if analysis.recommendation == AgentVote.SKIP:
                    # Skeptics often skip - question if too conservative
                    concerns = analysis.concerns
                    if len(concerns) <= 1:
                        critique_text = "May be overly conservative"
                        agreement = True  # But acknowledge
                        suggestions.append("Check if concerns are truly blocking")
            
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
        # Incorporate feedback about momentum sustainability
        new_findings = original_analysis.key_findings.copy()
        new_warnings = original_analysis.warnings.copy()
        
        for critique in critiques:
            ifcritique.to_agent == self.name and not critique.agreement:
                if "sustainability" in critique.critique_text.lower():
                    new_warnings.append("Momentum may be unsustainable")
        
        return Analysis(
            agent_name=self.name,
            perspective=self.perspective,
            recommendation=original_analysis.recommendation,
            confidence=original_analysis.confidence,
            reasoning=original_analysis.reasoning,
            key_findings=new_findings,
            warnings=new_warnings,
            concerns=original_analysis.concerns,
            supporting_evidence=original_analysis.supporting_evidence
        )