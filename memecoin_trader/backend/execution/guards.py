"""Capital protection guards - immutable rules."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class GuardAction(Enum):
    """Action taken by a guard."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"


@dataclass
class GuardResult:
    """Result of a guard check."""
    action: GuardAction
    guard_name: str
    message: str
    details: dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def is_blocked(self) -> bool:
        return self.action == GuardAction.BLOCK
    
    @property
    def is_allowed(self) -> bool:
        return self.action == GuardAction.ALLOW


class CapitalGuards:
    """Immutable capital protection rules."""
    
    # These CANNOT be overridden by AI
    MAX_POSITION_SIZE = 0.05  # 5% of portfolio
    DAILY_LOSS_LIMIT = 0.10    # 10% daily loss limit
    DRAWDOWN_PAUSE = 0.20      # 20% drawdown triggers pause
    MIN_CONFIDENCE = 0.70       # 70% minimum confidence
    
    def __init__(self):
        # Track daily stats (would persist in production)
        self._daily_loss = 0.0
        self._drawdown = 0.0
    
    def check_position_size(
        self,
        portfolio_value: float,
        proposed_position: float
    ) -> GuardResult:
        """Check if position size is within limits."""
        if portfolio_value <= 0:
            return GuardResult(
                action=GuardAction.BLOCK,
                guard_name="position_size",
                message="No portfolio value",
                details={"portfolio": portfolio_value, "position": proposed_position}
            )
        
        position_pct = proposed_position / portfolio_value
        
        if position_pct > self.MAX_POSITION_SIZE:
            return GuardResult(
                action=GuardAction.BLOCK,
                guard_name="position_size",
                message=f"Position {position_pct:.1%} exceeds max {self.MAX_POSITION_SIZE:.1%}",
                details={
                    "position_pct": position_pct,
                    "max_pct": self.MAX_POSITION_SIZE,
                    "portfolio": portfolio_value,
                    "position": proposed_position
                }
            )
        
        if position_pct > self.MAX_POSITION_SIZE * 0.8:
            return GuardResult(
                action=GuardAction.WARN,
                guard_name="position_size",
                message=f"Position {position_pct:.1%} near limit",
                details={"position_pct": position_pct}
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            guard_name="position_size",
            message=f"Position {position_pct:.1%} within limits",
            details={"position_pct": position_pct}
        )
    
    def check_daily_loss(
        self,
        daily_pnl_pct: float
    ) -> GuardResult:
        """Check if daily loss limit exceeded."""
        if daily_pnl_pct < -self.DAILY_LOSS_LIMIT:
            return GuardResult(
                action=GuardAction.BLOCK,
                guard_name="daily_loss",
                message=f"Daily loss {abs(daily_pnl_pct):.1%} exceeds limit",
                details={
                    "daily_pnl": daily_pnl_pct,
                    "limit": self.DAILY_LOSS_LIMIT
                }
            )
        
        if daily_pnl_pct < -self.DAILY_LOSS_LIMIT * 0.5:
            return GuardResult(
                action=GuardAction.WARN,
                guard_name="daily_loss",
                message=f"Daily loss at {abs(daily_pnl_pct):.1%}",
                details={"daily_pnl": daily_pnl_pct}
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            guard_name="daily_loss",
            message=f"Daily P&L {daily_pnl_pct:.1%} in limits",
            details={"daily_pnl": daily_pnl_pct}
        )
    
    def check_drawdown(
        self,
        drawdown: float
    ) -> GuardResult:
        """Check if drawdown pause triggered."""
        if drawdown > self.DRAWDOWN_PAUSE:
            return GuardResult(
                action=GuardAction.BLOCK,
                guard_name="drawdown",
                message=f"Drawdown {drawdown:.1%} triggers pause",
                details={
                    "drawdown": drawdown,
                    "limit": self.DRAWDOWN_PAUSE
                }
            )
        
        if drawdown > self.DRAWDOWN_PAUSE * 0.5:
            return GuardResult(
                action=GuardAction.WARN,
                guard_name="drawdown",
                message=f"Drawdown at {drawdown:.1%}",
                details={"drawdown": drawdown}
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            guard_name="drawdown",
            message=f"Drawdown {drawdown:.1%} safe",
            details={"drawdown": drawdown}
        )
    
    def check_confidence(
        self,
        confidence: float
    ) -> GuardResult:
        """Check if confidence is sufficient."""
        if confidence < self.MIN_CONFIDENCE:
            return GuardResult(
                action=GuardAction.BLOCK,
                guard_name="confidence",
                message=f"Confidence {confidence:.1%} below minimum",
                details={
                    "confidence": confidence,
                    "min": self.MIN_CONFIDENCE
                }
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            guard_name="confidence",
            message=f"Confidence {confidence:.1%} adequate",
            details={"confidence": confidence}
        )
    
    def check_all(
        self,
        portfolio_value: float,
        proposed_position: float,
        daily_pnl_pct: float,
        drawdown: float,
        confidence: float
    ) -> list[GuardResult]:
        """Run all guard checks."""
        results = []
        
        # Position size
        results.append(
            self.check_position_size(portfolio_value, proposed_position)
        )
        
        # Daily loss
        results.append(self.check_daily_loss(daily_pnl_pct))
        
        # Drawdown
        results.append(self.check_drawdown(drawdown))
        
        # Confidence
        results.append(self.check_confidence(confidence))
        
        return results
    
    def can_trade(
        self,
        portfolio_value: float,
        proposed_position: float,
        daily_pnl_pct: float,
        drawdown: float,
        confidence: float
    ) -> tuple[bool, str]:
        """Check if trade is allowed.
        
        Returns:
            (can_trade, reason)
        """
        results = self.check_all(
            portfolio_value,
            proposed_position,
            daily_pnl_pct,
            drawdown,
            confidence
        )
        
        # Check for any blocks
        blocked = [r for r in results if r.is_blocked]
        
        if blocked:
            return False, "; ".join(r.message for r in blocked)
        
        # Check for warnings
        warnings = [r for r in results if r.action == GuardAction.WARN]
        
        if warnings:
            return True, f"Warnings: {len(warnings)}"
        
        return True, "All checks passed"
    
    def reset_daily(self):
        """Reset daily tracking (call at start of new day)."""
        self._daily_loss = 0.0
    
    def update_daily_pnl(self, pnl_pct: float):
        """Update daily P&L."""
        self._daily_loss = pnl_pct


# Singleton guards instance
_guards: Optional[CapitalGuards] = None


def get_guards() -> CapitalGuards:
    """Get the global guards instance."""
    global _guards
    if _guards is None:
        _guards = CapitalGuards()
    return _guards