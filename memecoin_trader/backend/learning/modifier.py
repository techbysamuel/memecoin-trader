"""Filter modifier for auto-tuning."""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import json
from pathlib import Path
from datetime import datetime

from memecoin_trader.backend.learning.analyzer import FilterAnalyzer, FilterAnalysis


class ModificationRisk(Enum):
    """Risk level of modification."""
    LOW = "low"      # Auto-apply
    MEDIUM = "medium"  # Review required
    HIGH = "high"    # Manual only


@dataclass
class FilterModification:
    """Proposed filter modification."""
    filter_name: str
    parameter: str
    current_value: any
    proposed_value: any
    risk: ModificationRisk
    reason: str
    expected_improvement: float = 0.0  # Expected precision improvement
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "filter_name": self.filter_name,
            "parameter": self.parameter,
            "current_value": str(self.current_value),
            "proposed_value": str(self.proposed_value),
            "risk": self.risk.value,
            "reason": self.reason,
            "expected_improvement": self.expected_improvement,
            "created_at": self.created_at.isoformat()
        }


class FilterModifier:
    """Modifies filters based on performance."""
    
    def __init__(self, analyzer: FilterAnalyzer = None):
        self.analyzer = analyzer or FilterAnalyzer()
        self.modifications_log = Path("./data/modifications")
        self.modifications_log.mkdir(parents=True, exist_ok=True)
    
    def suggest_modifications(self) -> list[FilterModification]:
        """Analyze and suggest filter modifications."""
        analyses = self.analyzer.analyze_all_filters(days=30)
        
        suggestions = []
        
        for analysis in analyses:
            # Low precision - suggest parameter tuning
            if analysis.precision < 0.5 and analysis.total_evaluations > 10:
                # Suggest more conservative threshold
                mod = FilterModification(
                    filter_name=analysis.filter_name,
                    parameter="threshold",
                    current_value="unknown",
                    proposed_value="more_conservative",
                    risk=ModificationRisk.MEDIUM,
                    reason=f"Low precision {analysis.precision:.1%} suggests tightening",
                    expected_improvement=0.1
                )
                suggestions.append(mod)
            
            # High false positives
            elif analysis.false_positives > analysis.true_positives:
                mod = FilterModification(
                    filter_name=analysis.filter_name,
                    parameter="threshold",
                    current_value="unknown",
                    proposed_value="strict",
                    risk=ModificationRisk.LOW,
                    reason=f"False positives exceed true positives",
                    expected_improvement=0.05
                )
                suggestions.append(mod)
            
            # Very high precision - can relax
            elif analysis.precision > 0.85 and analysis.total_evaluations > 20:
                mod = FilterModification(
                    filter_name=analysis.filter_name,
                    parameter="threshold", 
                    current_value="unknown",
                    proposed_value="relaxed",
                    risk=ModificationRisk.LOW,
                    reason=f"High precision {analysis.precision:.1%} - room to relax",
                    expected_improvement=0.0
                )
                suggestions.append(mod)
        
        return suggestions
    
    def apply_low_risk_modifications(self) -> list[FilterModification]:
        """Apply low-risk modifications automatically."""
        suggestions = self.suggest_modifications()
        
        applied = []
        
        for suggestion in suggestions:
            if suggestion.risk == ModificationRisk.LOW:
                # Log the modification
                self._log_modification(suggestion)
                applied.append(suggestion)
        
        return applied
    
    def _log_modification(self, modification: FilterModification):
        """Log a modification."""
        filename = modification.filter_name + ".json"
        path = self.modifications_log / filename
        
        existing = []
        if path.exists():
            with open(path) as f:
                existing = json.load(f)
        
        existing.append(modification.to_dict())
        
        with open(path, "w") as f:
            json.dump(existing, f, indent=2)
    
    def get_pending_review(self) -> list[FilterModification]:
        """Get modifications needing review."""
        suggestions = self.suggest_modifications()
        return [s for s in suggestions if s.risk != ModificationRisk.LOW]
    
    def generate_proposal(
        self,
        filter_name: str,
        parameter: str,
        new_value: any,
        reason: str
    ) -> FilterModification:
        """Generate a modification proposal."""
        return FilterModification(
            filter_name=filter_name,
            parameter=parameter,
            current_value="current",
            proposed_value=str(new_value),
            risk=ModificationRisk.MEDIUM,
            reason=reason,
            expected_improvement=0.0
        )


# Singleton
_modifier: Optional[FilterModifier] = None


def get_modifier() -> FilterModifier:
    """Get the global modifier instance."""
    global _modifier
    if _modifier is None:
        _modifier = FilterModifier()
    return _modifier