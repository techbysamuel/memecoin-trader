"""Rug detection filter - detects common rug pull patterns."""

from dataclasses import dataclass
from typing import Optional
from memecoin_trader.backend.filters.base import Filter, FilterResult
from memecoin_trader.backend.core.config import settings


class RugDetectionFilter(Filter):
    """Filter for detecting rug pull patterns."""
    
    name = "rug_detection"
    description = "Detects common rug pull patterns"
    cost = 3.0  # More expensive - check for complex patterns
    
    async def evaluate(self, token_data: dict) -> FilterResult:
        """Evaluate token for rug patterns."""
        warnings = []
        issues = []
        
        # Check liquidity removal
        liquidity_change = token_data.get("liquidity_change_24h", 0)
        if liquidity_change < -0.5:  # More than 50% removed
            issues.append(f"Liquidity dropped {abs(liquidity_change):.1%} in 24h")
        
        # Check mint authority
        mint_authority = token_data.get("mint_authority")
        if mint_authority and mint_authority != "null":
            warnings.append("Mint authority not disabled")
        
        # Check freeze authority
        freeze_authority = token_data.get("freeze_authority")
        if freeze_authority and freeze_authority != "null":
            warnings.append("Freeze authority not disabled")
        
        # Check for transfer fees
        transfer_fee = token_data.get("transfer_fee", 0)
        if transfer_fee > 0:
            issues.append(f"Transfer fee of {transfer_fee}% detected")
        
        # Check if honeypot (can buy but can't sell)
        can_buy = token_data.get("can_buy", True)
        can_sell = token_data.get("can_sell", True)
        
        if can_buy and not can_sell:
            issues.append("Honeypot detected: can buy but cannot sell")
        
        # Check holder growth vs volume mismatch
        new_holders = token_data.get("new_holders_24h", 0)
        volume = token_data.get("volume_24h", 0)
        
        if new_holders > 100 and volume < 10000:
            warnings.append(f"High new holders ({new_holders}) but low volume")
        
        # Check for suspicious trade patterns
        buy_sell_ratio = token_data.get("buy_sell_ratio", 1.0)
        if buy_sell_ratio > 10:
            warnings.append(f"Unusual buy/sell ratio: {buy_sell_ratio:.1f}x")
        
        # Reject if critical issues found
        if issues:
            return FilterResult(
                passed=False,
                confidence=0.95,
                reason="; ".join(issues),
                details={
                    "issues": issues,
                    "warnings": warnings,
                    "liquidity_change": liquidity_change,
                    "transfer_fee": transfer_fee
                }
            )
        
        return FilterResult(
            passed=True,
            confidence=0.85 if not warnings else 0.70,
            reason="No critical rug patterns detected",
            details={
                "warnings": warnings,
                "liquidity_change": liquidity_change
            },
            warnings=warnings
        )


@dataclass
class RugCheck:
    """Individual rug check result."""
    check_name: str
    passed: bool
    severity: str  # "critical", "warning", "info"
    description: str
    
    def is_critical(self) -> bool:
        return self.severity == "critical" and not self.passed