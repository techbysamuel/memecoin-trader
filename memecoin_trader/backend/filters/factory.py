"""Filter factory for creating and managing filters."""

from typing import Optional, Type
from dataclasses import dataclass, field

from memecoin_trader.backend.filters.base import Filter, FilterResult
from memecoin_trader.backend.filters.liquidity_filter import LiquidityFilter
from memecoin_trader.backend.filters.holder_filter import HolderFilter
from memecoin_trader.backend.filters.rug_detection_filter import RugDetectionFilter
from memecoin_trader.backend.filters.volume_filter import VolumeFilter


# Filter registry
FILTER_REGISTRY: dict[str, Type[Filter]] = {
    "liquidity": LiquidityFilter,
    "holder_concentration": HolderFilter,
    "rug_detection": RugDetectionFilter,
    "volume": VolumeFilter,
}


@dataclass
class FilterPipeline:
    """Chain of filters to evaluate tokens."""
    
    filters: list[Filter] = field(default_factory=list)
    _enabled_filters: dict[str, bool] = field(default_factory=dict)
    
    def __init__(self, filter_names: list[str] = None):
        """Create pipeline with specified filters.
        
        Args:
            filter_names: List of filter names to include. 
                       If None, uses all default filters.
        """
        self.filters = []
        self._enabled_filters = {}
        
        if filter_names is None:
            filter_names = list(FILTER_REGISTRY.keys())
        
        for name in filter_names:
            if name in FILTER_REGISTRY:
                filter_instance = FILTER_REGISTRY[name]()
                self.filters.append(filter_instance)
                self._enabled_filters[name] = True
    
    def add_filter(self, filter_instance: Filter):
        """Add a filter to the pipeline."""
        self.filters.append(filter_instance)
        self._enabled_filters[filter_instance.name] = True
    
    def remove_filter(self, name: str):
        """Remove a filter from the pipeline."""
        self.filters = [f for f in self.filters if f.name != name]
        self._enabled_filters.pop(name, None)
    
    def enable_filter(self, name: str):
        """Enable a filter."""
        self._enabled_filters[name] = True
    
    def disable_filter(self, name: str):
        """Disable a filter."""
        self._enabled_filters[name] = False
    
    def is_enabled(self, name: str) -> bool:
        """Check if filter is enabled."""
        return self._enabled_filters.get(name, False)
    
    async def evaluate(self, token_data: dict) -> list[FilterResult]:
        """Run all filters on token data.
        
        Returns list of results in evaluation order.
        Filters are sorted by cost (cheapest first).
        """
        # Sort by cost
        sorted_filters = sorted(
            self.filters,
            key=lambda f: f.cost
        )
        
        results = []
        
        for filter in sorted_filters:
            if not self.is_enabled(filter.name):
                continue
            
            result = await filter.evaluate(token_data)
            results.append(result)
            
            # Early exit on first failure
            if not result.passed:
                break
        
        return results
    
    def get_passed_filters(self, results: list[FilterResult]) -> list[Filter]:
        """Get list of filters that passed."""
        passed = []
        for i, result in enumerate(results):
            if result.passed and i < len(self.filters):
                passed.append(self.filters[i])
        return passed
    
    def get_failed_filter(self, results: list[FilterResult]) -> Optional[Filter]:
        """Get the first filter that failed."""
        for i, result in enumerate(results):
            if not result.passed and i < len(self.filters):
                return self.filters[i]
        return None
    
    def get_overall_confidence(self, results: list[FilterResult]) -> float:
        """Calculate overall confidence from all filter results."""
        if not results:
            return 0.0
        
        # Weight by filter importance
        total_weight = sum(f.weight for f in self.filters if f.is_enabled)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            r.confidence * f.weight 
            for r, f in zip(results, self.filters)
            if f.is_enabled
        )
        
        return weighted_sum / total_weight
    
    def to_dict(self) -> dict:
        """Serialize pipeline configuration."""
        return {
            "filters": [f.to_dict() for f in self.filters],
            "enabled": self._enabled_filters
        }


def create_filter(name: str, **kwargs) -> Filter:
    """Create a filter by name."""
    if name not in FILTER_REGISTRY:
        raise ValueError(f"Unknown filter: {name}")
    return FILTER_REGISTRY[name](**kwargs)


def get_available_filters() -> list[str]:
    """Get list of available filter names."""
    return list(FILTER_REGISTRY.keys())


def get_filter_info(name: str) -> dict:
    """Get filter information."""
    if name not in FILTER_REGISTRY:
        return {}
    
    filter_class = FILTER_REGISTRY[name]
    return {
        "name": filter_class.name,
        "description": filter_class.description,
        "cost": filter_class.cost,
        "weight": filter_class.weight
    }