"""Wallet tracker agent - focuses on smart money tracking."""

from dataclasses import dataclass
from typing import Optional
from memecoin_trader.backend.agents.base import (
    TradingAgent,
    Analysis,
    Critique,
    AgentVote,
    AgentContext
)


class WalletTrackerAgent(TradingAgent):
    """Agent that tracks smart money wallets."""
    
    name = "wallet_tracker"
    perspective = "Smart money tracking"
    description = "Tracks known profitable wallets and identifies smart money positions"
    
    async def analyze(self, token_data: dict, context: dict) -> Analysis:
        """Analyze token for smart money positions."""
        findings = []
        warnings = []
        concerns = []
        evidence = {}
        
        # Check for known degen wallets
        known_wallets = token_data.get("known_degen_wallets", [])
        smart_money_count = len(known_wallets)
        
        if smart_money_count >= 3:
            findings.append(f"Smart money entering: {smart_money_count} known wallets")
            evidence["smart_money_count"] = smart_money_count
            evidence["wallets"] = known_wallets[:5]
        elif smart_money_count >= 1:
            findings.append(f"Some smart money detected: {smart_money_count}")
            evidence["smart_money_count"] = smart_money_count
        else:
            warnings.append("No known smart money detected")
            evidence["smart_money_count"] = 0
        
        # Check for top trader positions
        top_traders = token_data.get("top_trader_positions", [])
        if top_traders:
            total_position = sum(t.get("sol_value", 0) for t in top_traders)
            if total_position > 10:  # 10+ SOL in top trader positions
                findings.append(f"Top trader position: {total_position:.1f} SOL")
                evidence["top_trader_sol"] = total_position
            elif total_position > 0:
                evidence["top_trader_sol"] = total_position
        
        # Check recent big buyers
        big_buyers = token_data.get("big_buyers_24h", [])
        if big_buyers:
            total_buy = sum(b.get("sol_amount", 0) for b in big_buyers)
            if total_buy > 5:
                findings.append(f"Big buyers: {total_buy:.1f} SOL in 24h")
                evidence["big_buyers_sol"] = total_buy
        
        # Check wallet growth
        new_wallets_24h = token_data.get("new_wallets_24h", 0)
        if new_wallets_24h > 100:
            findings.append(f"Strong wallet growth: {new_wallets_24h}")
            evidence["new_wallets_24h"] = new_wallets_24h
        elif new_wallets_24h > 20:
            warnings.append(f"Moderate wallet growth: {new_wallets_24h}")
            evidence["new_wallets_24h"] = new_wallets_24h
        
        # Check if any famous traders are in
        trader_mentions = token_data.get("trader_mentions", [])
        if trader_mentions:
            findings.append(f"Traders mentioned: {', '.join(trader_mentions[:3])}")
            evidence["trader_mentions"] = trader_mentions
        
        # Determine recommendation
        score = smart_money_count + (len(findings) - len(warnings))
        
        if smart_money_count >= 3:
            recommendation = AgentVote.BUY
            confidence = 0.85
            reasoning = f"Strong smart money entry: {smart_money_count} known wallets"
        elif smart_money_count >= 1 and len(findings) >= 1:
            recommendation = AgentVote.BUY
            confidence = 0.70
            reasoning = f"Smart money present: {findings[0]}"
        elif smart_money_count >= 1:
            recommendation = AgentVote.UNCERTAIN
            confidence = 0.50
            reasoning = "Limited smart money confirmation"
        else:
            recommendation = AgentVote.SKIP
            confidence = 0.65
            reasoning = "No smart money detected - proceed with caution"
        
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
            
            # Challenge skeptic
            if analysis.agent_name == "skeptic":
                # If skipping, verify if it's due to valid smart money absence
                if analysis.recommendation == AgentVote.SKIP:
                    # Skeptics skip - check if they miss smart money
                    evidence = analysis.supporting_evidence
                    concerns = analysis.concerns
                    if len(concerns) <= 2 and "smart money" in analysis.reasoning.lower():
                        critique_text = "Smart money may not be the only signal"
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
        new_findings = original_analysis.key_findings.copy()
        new_warnings = original_analysis.warnings.copy()
        
        # Adjust confidence based on wallet quality
        evidence = original_analysis.supporting_evidence
        smart_money_count = evidence.get("smart_money_count", 0)
        
        for critique in critiques:
            # If skeptic has valid concerns, add warning
            ifnot critique.to_agent == self.name and not critique.agreement:
                new_warnings.append("Smart money could be exit liquidity")
        
        confidence = original_analysis.confidence
        if new_warnings:
            confidence = max(0.5, confidence - 0.1)
        
        return Analysis(
            agent_name=self.name,
            perspective=self.perspective,
            recommendation=original_analysis.recommendation,
            confidence=confidence,
            reasoning=original_analysis.reasoning,
            key_findings=new_findings,
            warnings=new_warnings,
            concerns=original_analysis.concerns,
            supporting_evidence=evidence
        )