"""Volume filter - detects volume spikes and wash trading."""

from dataclasses import dataclass
from typing import Optional
from memecoin_trader.backend.filters.base import Filter, FilterResult
from memecoin_trader.backend.core.config import settings


class VolumeFilter(Filter):
    """Filter tokens by volume patterns."""
    
    name = "volume"
    description = "Requires minimum volume spike"
    cost = 2.0  # Moderate cost
    
    def __init__(
        self,
        min_volume_spike: float = None,
        warn_threshold: float = None
    ):
        super().__init__()
        self.min_volume_spike = min_volume_spike or settings.filters.min_volume_spike
        self.warn_threshold = warn_threshold or settings.filters.volume_warn_threshold
    
    async def evaluate(self, token_data: dict) -> FilterResult:
        """Evaluate token volume."""
        current_volume = token_data.get("volume_24h", 0)
        baseline_volume = token_data.get("baseline_volume", 0)
        
        warnings = []
        
        # Need baseline to compare
        if baseline_volume == 0:
            # New token without history - use current as baseline
            if current_volume < settings.filters.min_liquidity:
                return FilterResult(
                    passed=False,
                    confidence=0.80,
                    reason="No volume history - cannot verify spike",
                    details={"current_volume": current_volume}
                )
            # New but well funded
            return FilterResult(
                passed=True,
                confidence=0.70,
                reason="New token with sufficient volume",
                details={"current_volume": current_volume},
                warnings=["No baseline for comparison"]
            )
        
        # Calculate volume spike
        volume_ratio = current_volume / baseline_volume if baseline_volume > 0 else 0
        
        # Check for wash trading (unusual volume with flat price)
        price_change = abs(token_data.get("price_change_24h", 0))
        
        if volume_ratio > self.min_volume_spike:
            # High volume spike - check if price follows
            if volume_ratio > 5 and price_change < 0.01:
                warnings.append("High volume but minimal price change - possible wash trading")
            
            # Check volume/holder ratio
            new_holders = token_data.get("new_holders_24h", 0)
            if new_holders > 0:
                vol_per_holder = current_volume / new_holders
                if vol_per_holder > 100000:  # Unusual volume per new holder
                    warnings.append(
                        f"High volume per new holder: ${vol_per_holder:.2f}"
                    )
            
            return FilterResult(
                passed=True,
                confidence=0.85,
                reason=f"Volume spike {volume_ratio:.1f}x detected",
                details={
                    "current_volume": current_volume,
                    "baseline_volume": baseline_volume,
                    "volume_ratio": volume_ratio,
                    "price_change": price_change
                },
                warnings=warnings
            )
        
        # Check warning zone
        if volume_ratio > self.warn_threshold:
            warnings.append(
                f"Volume {volume_ratio:.1f}x above warning threshold"
            )
            return FilterResult(
                passed=True,
                confidence=0.60,
                reason="Volume in warning zone",
                details={
                    "volume_ratio": volume_ratio,
                    "warn_threshold": self.warn_threshold
                },
                warnings=warnings
            )
        
        # No volume spike
        return FilterResult(
            passed=False,
            confidence=0.90,
            reason=f"Volume spike {volume_ratio:.1f}x below minimum {self.min_volume_spike}x",
            details={
                "current_volume": current_volume,
                "baseline_volume": baseline_volume,
                "volume_ratio": volume_ratio,
                "threshold": self.min_volume_spike
            }
        )


@dataclass
class VolumeProfile:
    """Volume profile for a token."""
    volume_24h: float
    volume_7d_avg: float
    volume_change_pct: float
    buy_volume: float
    sell_volume: float
    trade_count: int
    
    @property
    def buy_sell_ratio(self) -> float:
        if self.sell_volume == 0:
            return float('inf') if self.buy_volume > 0 else 0
        return self.buy_volume / self.sell_volume