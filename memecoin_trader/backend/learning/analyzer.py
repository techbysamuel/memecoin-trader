"""Filter performance analyzer."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from memecoin_trader.backend.learning.recorder import TradeRecorder, TradeRecord
from memecoin_trader.backend.filters.base import FilterPerformance


@dataclass
class FilterAnalysis:
    """Analysis of a filter's performance."""
    filter_name: str
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    total_evaluations: int = 0
    true_positives: int = 0
    false_positives: int = 0
    
    # Trend
    precision_trend: float = 0.0  # Change over time
    
    def to_dict(self) -> dict:
        return {
            "filter_name": self.filter_name,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "total_evaluations": self.total_evaluations,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "precision_trend": self.precision_trend
        }


class FilterAnalyzer:
    """Analyzes filter performance over time."""
    
    def __init__(self, recorder: TradeRecorder = None):
        self.recorder = recorder or TradeRecorder()
    
    def analyze_filter(
        self,
        filter_name: str,
        days: int = 30
    ) -> FilterAnalysis:
        """Analyze a specific filter's performance.
        
        Args:
            filter_name: Name of the filter
            days: Number of days to analyze
            
        Returns:
            FilterAnalysis with metrics
        """
        trades = self.recorder.get_records_with_outcome()
        
        # Filter to time range
        cutoff = datetime.utcnow() - timedelta(days=days)
        trades = [t for t in trades if t.created_at >= cutoff]
        
        if not trades:
            return FilterAnalysis(filter_name=filter_name)
        
        # Analyze based on filter results and outcome
        tp = 0  # Filter PASSED and trade was profitable
        fp = 0  # Filter PASSED but trade lost money
        fn = 0  # Filter FAILED but trade would have been profitable
        
        for trade in trades:
            # Get filter result for this filter
            filter_result = trade.filter_results.get(filter_name)
            
            if filter_result is None:
                continue
            
            predicted_pass = filter_result.get("passed", True)
            was_profitable = trade.realized_pnl > 0
            
            if predicted_pass and was_profitable:
                tp += 1
            elif predicted_pass and not was_profitable:
                fp += 1
            elif not predicted_pass and was_profitable:
                fn += 1
        
        total = tp + fp + fn
        
        if total == 0:
            return FilterAnalysis(filter_name=filter_name)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return FilterAnalysis(
            filter_name=filter_name,
            precision=precision,
            recall=recall,
            f1_score=f1,
            total_evaluations=total,
            true_positives=tp,
            false_positives=fp
        )
    
    def analyze_all_filters(self, days: int = 30) -> list[FilterAnalysis]:
        """Analyze all filters."""
        filter_names = ["liquidity", "holder_concentration", "rug_detection", "volume"]
        
        analyses = []
        for name in filter_names:
            analysis = self.analyze_filter(name, days)
            analyses.append(analysis)
        
        return analyses
    
    def get_recommendations(self, days: int = 30) -> list[dict]:
        """Get filter improvement recommendations."""
        analyses = self.analyze_all_filters(days)
        
        recommendations = []
        
        for analysis in analyses:
            rec = {"filter": analysis.filter_name}
            
            if analysis.precision < 0.5:
                rec["action"] = "review"
                rec["reason"] = f"Low precision {analysis.precision:.1%}"
                rec["priority"] = "high"
            elif analysis.precision < 0.6:
                rec["action"] = "tune"
                rec["reason"] = f"Below target precision"
                rec["priority"] = "medium"
            elif analysis.precision > 0.8:
                rec["action"] = "keep"
                rec["reason"] = f"Strong precision {analysis.precision:.1%}"
                rec["priority"] = "low"
            else:
                rec["action"] = "keep"
                rec["reason"] = "Adequate performance"
                rec["priority"] = "low"
            
            recommendations.append(rec)
        
        return sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["priority"]])
    
    def get_performance_summary(self, days: int = 30) -> dict:
        """Get overall performance summary."""
        analyses = self.analyze_all_filters(days)
        
        stats = self.recorder.get_stats()
        
        return {
            "stats": stats,
            "filter_analyses": [a.to_dict() for a in analyses],
            "recommendations": self.get_recommendations(days)
        }


# Singleton
_analyzer: Optional[FilterAnalyzer] = None


def get_analyzer() -> FilterAnalyzer:
    """Get the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = FilterAnalyzer()
    return _analyzer