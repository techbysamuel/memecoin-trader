"""Custom exceptions for memecoin trading system."""

from typing import Optional, Any


class MemecoinTraderError(Exception):
    """Base exception for all trading system errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIError(MemecoinTraderError):
    """Base exception for API-related errors."""
    pass


class RPCError(APIError):
    """Error communicating with RPC provider."""
    pass


class BirdeyeError(APIError):
    """Error from Birdeye API."""
    pass


class GMGNFError(APIError):
    """Error from GMGN API."""
    pass


class JupiterError(APIError):
    """Error from Jupiter API."""
    pass


class FilterError(MemecoinTraderError):
    """Base exception for filter errors."""
    pass


class FilterTimeoutError(FilterError):
    """Filter took too long to evaluate."""
    pass


class FilterDataError(FilterError):
    """Filter received invalid data."""
    pass


class AgentError(MemecoinTraderError):
    """Base exception for agent errors."""
    pass


class AgentAPIError(AgentError):
    """Error from LLM API."""
    pass


class DebateError(MemecoinTraderError):
    """Error in debate protocol."""
    pass


class NoConsensusError(DebateError):
    """Agents failed to reach consensus."""
    
    def __init__(self, token: str, votes: dict):
        super().__init__(
            f"No consensus for {token}: {votes}",
            details={"votes": votes, "token": token}
        )
        self.votes = votes


class ExecutionError(MemecoinTraderError):
    """Base exception for execution errors."""
    pass


class InsufficientBalanceError(ExecutionError):
    """Insufficient balance for trade."""
    
    def __init__(self, required: float, available: float):
        super().__init__(
            f"Insufficient balance: need {required}, have {available}",
            details={"required": required, "available": available}
        )
        self.required = required
        self.available = available


class SlippageError(ExecutionError):
    """Trade exceeded slippage tolerance."""
    pass


class GuardError(ExecutionError):
    """Capital protection guard blocked trade."""
    
    def __init__(self, guard_name: str, reason: str):
        super().__init__(
            f"Guard '{guard_name}' blocked trade: {reason}",
            details={"guard": guard_name, "reason": reason}
        )
        self.guard_name = guard_name


class PositionSizeError(GuardError):
    """Position size exceeds limit."""
    
    def __init__(self, size: float, max_size: float):
        super().__init__(
            "position_size",
            f"Position {size:.2%} exceeds max {max_size:.2%}"
        )
        self.size = size
        self.max_size = max_size


class DailyLossError(GuardError):
    """Daily loss limit exceeded."""
    
    def __init__(self, loss: float, limit: float):
        super().__init__(
            "daily_loss",
            f"Daily loss {loss:.2%} exceeds limit {limit:.2%}"
        )
        self.loss = loss
        self.limit = limit


class DrawdownError(GuardError):
    """Drawdown pause triggered."""
    
    def __init__(self, drawdown: float, limit: float):
        super().__init__(
            "drawdown",
            f"Drawdown {drawdown:.2%} exceeds limit {limit:.2%}"
        )
        self.drawdown = drawdown
        self.limit = limit


class LearningError(MemecoinTraderError):
    """Base exception for learning loop errors."""
    pass


class DataError(MemecoinTraderError):
    """Base exception for data errors."""
    pass


class WalletError(MemecoinTraderError):
    """Wallet-related error."""
    pass