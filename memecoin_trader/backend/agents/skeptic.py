"""Skeptic agent - focuses on exit traps and rug indicators."""

from dataclasses import dataclass
from typing import Optional
from memecoin_trader.backend.agents.base import (
    TradingAgent,
    Analysis,
    Critique,
    AgentVote,
    AgentContext
)


class SkepticAgent(TradingAgent):
    """Agent that focuses on exit traps and rug indicators."""
    
    name = "skeptic"
    perspective = "Exit strategy and rug detection"
    description = "Questions the trade from a risk standpoint, looking for exit traps and suspicious patterns"
    
    async def analyze(self, token_data: dict, context: dict) -> Analysis:
        """Analyze token for exit trap patterns."""
        findings = []
        concerns = []
        warnings = []
        evidence = {}
        
        # Check liquidity
        liquidity = token_data.get("liquidity_usd", 0)
        if liquidity < 50000:
            concerns.append(f"Low liquidity: ${liquidity:,.2f}")
            findings.append("Liquidity below safe threshold")
            evidence["liquidity"] = liquidity
        
        # Check holder concentration
        top10 = token_data.get("top10_concentration", 0)
        if top10 > 0.60:
            concerns.append(f"Top 10 holders: {top10:.1%}")
            findings.append("High holder concentration - exit risk")
            evidence["top10_concentration"] = top10
        
        # Check for honeypot
        can_buy = token_data.get("can_buy", True)
        can_sell = token_data.get("can_sell", True)
        if can_buy and not can_sell:
            concerns.append("Honeypot pattern detected")
            findings.append("Cannot sell - honeypot")
            evidence["can_buy"] = can_buy
            evidence["can_sell"] = can_sell
        
        # Check recent liquidity change
        liq_change = token_data.get("liquidity_change_24h", 0)
        if liq_change < -0.3:
            concerns.append(f"Liquidity down {abs(liq_change):.1%} in 24h")
            findings.append("Recent liquidity drain")
            evidence["liquidity_change"] = liq_change
        
        # Check for transfer fees
        transfer_fee = token_data.get("transfer_fee", 0)
        if transfer_fee > 0:
            concerns.append(f"Transfer fee: {transfer_fee}%")
            findings.append("Hidden fees detected")
            evidence["transfer_fee"] = transfer_fee
        
        # Check mint authority
        mint_auth = token_data.get("mint_authority")
        if mint_auth and mint_auth != "null":
            concerns.append("Mint authority not disabled")
            findings.append("Minting risk")
            evidence["mint_authority"] = mint_auth
        
        # Check token age
        token_age = token_data.get("token_age_hours", 0)
        if token_age < 1:
            warnings.append("Token less than 1 hour old")
            evidence["token_age_hours"] = token_age
        elif token_age < 24:
            warnings.append("Token less than 24 hours old")
        
        # Determine recommendation
        if concerns:
            recommendation = AgentVote.SKIP
            confidence = 0.85 if len(concerns) >= 2 else 0.75
            reasoning = f"Skipping due to {len(concerns)} concern(s): {', '.join(concerns[:2])}"
        else:
            recommendation = AgentVote.BUY
            confidence = 0.65 if warnings else 0.75
            reasoning = "No critical concerns identified" if not concerns else "Minor warnings only"
        
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
            
            # If momentum agent is bullish, question sustainability
            if analysis.agent_name == "momentum":
                if analysis.recommendation == AgentVote.BUY:
                    # Check for sustainable drivers
                    evidence = analysis.supporting_evidence
                    volume = evidence.get("volume_spike", 0)
                    if volume > 10:
                        critique_text = "Volume spike may be artificial/pump dump"
                        agreement = False
                        suggestions.append("Verify with wallet tracking")
                        counter["volume_sustainability"] = "unverified"
            
            # If wallet tracker is bullish, add caution
            elif analysis.agent_name == "wallet_tracker":
                if analysis.recommendation == AgentVote.BUY:
                    evidence = analysis.supporting_evidence
                    smart_money_count = evidence.get("smart_money_count", 0)
                    if smart_money_count < 3:
                        critique_text = "Limited smart money confirmation"
                        agreement = False if smart_money_count == 0 else True
                        suggestions.append("Wait for more smart money entries")
            
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
        # Skeptic stays skeptical
        return original_analysis