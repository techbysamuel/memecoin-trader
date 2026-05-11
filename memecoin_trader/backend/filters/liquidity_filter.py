"""Liquidity filter - rejects tokens with insufficient liquidity."""

from dataclasses import dataclass
from memecoin_trader.backend.filters.base import Filter, FilterResult
from memecoin_trader.backend.core.config import settings


class LiquidityFilter(Filter):
    """Filter tokens by liquidity threshold."""
    
    name = "liquidity"
    description = "Rejects tokens with insufficient liquidity"
    cost = 1.0  # Cheapest - check first
    
    def __init__(
        self,
        min_liquidity: float = None,
        warning_threshold: float = None
    ):
        super().__init__()
        self.min_liquidity = min_liquidity or settings.filters.min_liquidity
        self.warning_threshold = warning_threshold or settings.filters.liquidity_warning
    
    async def evaluate(self, token_data: dict) -> FilterResult:
        """Evaluate token liquidity."""
        # Get liquidity from token data
        liquidity = token_data.get("liquidity", 0)
        liquidity_usd = token_data.get("liquidity_usd", liquidity)
        
        warnings = []
        
        # Check if liquidity is too low
        if liquidity_usd < self.min_liquidity:
            return FilterResult(
                passed=False,
                confidence=0.95,
                reason=f"Liquidity ${liquidity_usd:.2f} below threshold ${self.min_liquidity:.2f}",
                details={
                    "liquidity": liquidity,
                    "liquidity_usd": liquidity_usd,
                    "threshold": self.min_liquidity
                }
            )
        
        # Warning zone
        if liquidity_usd < self.warning_threshold:
            warnings.append(
                f"Liquidity ${liquidity_usd:.2f} in warning zone"
            )
        
        return FilterResult(
            passed=True,
            confidence=0.85,
            reason=f"Liquidity ${liquidity_usd:.2f} adequate",
            details={
                "liquidity": liquidity,
                "liquidity_usd": liquidity_usd,
                "threshold": self.min_liquidity
            },
            warnings=warnings
        )


@dataclass
class LiquidityPool:
    """Liquidity pool information."""
    dex: str  # Raydium, Orca, etc.
    liquidity: float
    liquidity_usd: float
    volume_24h: float
    mint_a: str
    mint_b: str