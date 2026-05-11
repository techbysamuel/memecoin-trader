"""Structured logging for memecoin trading system."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        if self.include_extra and record.__dict__:
            extra = {
                k: v for k, v in record.__dict__.items()
                if not k.startswith("_") and k not in (
                    "name", "msg", "args", "created", "filename", 
                    "levelname", "levelno", "lineno", "module",
                    "msecs", "pathname", "process", "processName",
                    "relativeCreated", "thread", "threadName", "exc_info",
                    "exc_text", "stack_info", "funcName", "message"
                )
            }
            if extra:
                log_obj["extra"] = extra
        
        return json.dumps(log_obj)


class TradeLogger:
    """Specialized logger for trade events."""
    
    def __init__(self, name: str = "memecoin_trader.trades"):
        self.logger = logging.getLogger(name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False
    
    def log_signal(self, token: str, action: str, confidence: float, **kwargs):
        """Log a trading signal."""
        self.logger.info(
            f"TRADE_SIGNAL: {action} {token}",
            extra={
                "event_type": "trade_signal",
                "token_address": token,
                "action": action,
                "confidence": confidence,
                **kwargs
            }
        )
    
    def log_debate(self, token: str, round_num: int, agent: str, vote: str, **kwargs):
        """Log agent debate."""
        self.logger.info(
            f"DEBATE: Round {round_num} {agent} -> {vote}",
            extra={
                "event_type": "debate",
                "round": round_num,
                "agent": agent,
                "vote": vote,
                **kwargs
            }
        )
    
    def log_filter(self, token: str, filter_name: str, passed: bool, **kwargs):
        """Log filter evaluation."""
        self.logger.info(
            f"FILTER: {filter_name} {'PASS' if passed else 'FAIL'}",
            extra={
                "event_type": "filter",
                "token_address": token,
                "filter": filter_name,
                "passed": passed,
                **kwargs
            }
        )
    
    def log_execution(self, token: str, action: str, amount: float, **kwargs):
        """Log trade execution."""
        self.logger.info(
            f"EXECUTION: {action} {amount} SOL worth of {token}",
            extra={
                "event_type": "execution",
                "token_address": token,
                "action": action,
                "amount_sol": amount,
                **kwargs
            }
        )
    
    def log_error(self, error_type: str, message: str, **kwargs):
        """Log an error."""
        self.logger.error(
            f"ERROR: {error_type} - {message}",
            extra={
                "event_type": "error",
                "error_type": error_type,
                **kwargs
            }
        )


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False
) -> None:
    """Setup main application logging."""
    root_logger = logging.getLogger("memecoin_trader")
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)


# Default logger instances
trade_logger = TradeLogger()
main_logger = logging.getLogger("memecoin_trader")