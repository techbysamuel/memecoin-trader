"""Holder concentration filter - rejects tokens with high holder concentration."""

from dataclasses import dataclass
from memecoin_trader.backend.filters.base import Filter, FilterResult
from memecoin_trader.backend.core.config import settings


class HolderFilter(Filter):
    """Filter tokens by holder concentration."""
    
    name = "holder_concentration"
    description = "Rejects tokens with high holder concentration"
    cost = 2.0  # Moderate cost
    
    def __init__(
        self,
        max_top10_pct: float = None,
        top10_warning: float = None,
        single_holder_warning: float = None
    ):
        super().__init__()
        self.max_top10_pct = max_top10_pct or settings.filters.max_top10_holder_pct
        self.top10_warning = top10_warning or settings.filters.top10_holder_warning
        self.single_holder_warning = single_holder_warning or settings.filters.single_holder_warning
    
    async def evaluate(self, token_data: dict) -> FilterResult:
        """Evaluate token holder distribution."""
        # Get holder data
        holders = token_data.get("holders", [])
        top10_pct = token_data.get("top10_concentration", 0)
        
        # Find top holder percentage
        top_holder_pct = 0
        if holders:
            sorted_holders = sorted(holders, key=lambda h: h.get("pct", 0), reverse=True)
            top_holder_pct = sorted_holders[0].get("pct", 0) if sorted_holders else 0
        
        warnings = []
        
        # Check top 10 concentration
        if top10_pct > self.max_top10_pct:
            return FilterResult(
                passed=False,
                confidence=0.95,
                reason=f"Top 10 holders {top10_pct:.1%} exceeds {self.max_top10_pct:.1%}",
                details={
                    "top10_concentration": top10_pct,
                    "threshold": self.max_top10_pct,
                    "holder_count": len(holders)
                }
            )
        
        # Warning for high top 10
        if top10_pct > self.top10_warning:
            warnings.append(
                f"Top 10 holders {top10_pct:.1%} above warning threshold"
            )
        
        # Warning for single whale
        if top_holder_pct > self.single_holder_warning:
            warnings.append(
                f"Single holder {top_holder_pct:.1%} above warning threshold"
            )
        
        return FilterResult(
            passed=True,
            confidence=0.80,
            reason=f"Holder distribution acceptable",
            details={
                "top10_concentration": top10_pct,
                "top_holder_concentration": top_holder_pct,
                "holder_count": len(holders)
            },
            warnings=warnings
        )


@dataclass
class Holder:
    """Token holder information."""
    address: str
    balance: float
    pct: float  # Percentage of total supply
    is_contract: bool = False