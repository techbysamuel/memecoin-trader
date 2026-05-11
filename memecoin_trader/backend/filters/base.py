"""Filter base class for the filter pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
import json
from pathlib import Path


@dataclass
class FilterResult:
    """Result of a filter evaluation."""
    passed: bool
    confidence: float  # 0.0 to 1.0
    reason: str
    details: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "confidence": self.confidence,
            "reason": self.reason,
            "details": self.details,
            "warnings": self.warnings
        }


@dataclass
class FilterPerformance:
    """Historical performance of a filter."""
    total_evaluations: int = 0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1_score(self) -> float:
        """F1 score."""
        precision = self.precision
        recall = self.recall
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def record_outcome(self, predicted_pass: bool, actual_outcome: bool):
        """Record an evaluation outcome."""
        self.total_evaluations += 1
        if predicted_pass and actual_outcome:
            self.true_positives += 1
        elif predicted_pass and not actual_outcome:
            self.false_positives += 1
        elif not predicted_pass and actual_outcome:
            self.false_negatives += 1
        else:
            self.true_negatives += 1
    
    def to_dict(self) -> dict:
        return {
            "total_evaluations": self.total_evaluations,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score
        }
    
    def save(self, path: Path):
        """Save performance to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> "FilterPerformance":
        """Load performance from file."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        perf = cls()
        for key, value in data.items():
            if hasattr(perf, key):
                setattr(perf, key, value)
        return perf


class Filter(ABC):
    """Base class for all filters."""
    
    name: str = "base_filter"
    description: str = "Base filter"
    cost: float = 1.0  # Computational cost (1-10)
    weight: float = 1.0  # Importance weight
    expiry_condition: Optional[str] = None  # When to auto-deprecate
    
    def __init__(self):
        self._performance = FilterPerformance()
        self._enabled = True
    
    @abstractmethod
    async def evaluate(self, token_data: dict) -> FilterResult:
        """Evaluate a token against this filter.
        
        Args:
            token_data: Token data dictionary
            
        Returns:
            FilterResult with pass/fail and details
        """
        pass
    
    def get_performance(self) -> FilterPerformance:
        """Get filter performance metrics."""
        return self._performance
    
    def record_outcome(self, predicted_pass: bool, actual_outcome: bool):
        """Record the outcome for learning."""
        self._performance.record_outcome(predicted_pass, actual_outcome)
    
    @property
    def is_enabled(self) -> bool:
        """Check if filter is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable this filter."""
        self._enabled = True
    
    def disable(self):
        """Disable this filter."""
        self._enabled = False
    
    def to_dict(self) -> dict:
        """Serialize filter configuration."""
        return {
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "weight": self.weight,
            "enabled": self._enabled,
            "performance": self._performance.to_dict()
        }


# Type alias for filter results
TokenData = dict