"""Configuration management for memecoin trading system."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class APIConfig(BaseModel):
    """API configuration."""
    helius_rpc_url: str = Field(default="")
    quicknode_rpc_url: str = Field(default="")
    birdeye_api_key: str = Field(default="")
    gmgn_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    helius_rpc_key: str = Field(default="")


class FilterConfig(BaseModel):
    """Filter threshold configuration."""
    min_liquidity: float = Field(default=30_000, description="Minimum liquidity in USD")
    liquidity_warning: float = Field(default=50_000, description="Liquidity warning threshold")
    max_top10_holder_pct: float = Field(default=0.70, description="Max top 10 holders percentage")
    top10_holder_warning: float = Field(default=0.50, description="Top 10 holders warning")
    single_holder_warning: float = Field(default=0.30, description="Single holder warning")
    min_volume_spike: float = Field(default=5.0, description="Minimum volume spike multiplier")
    volume_warn_threshold: float = Field(default=3.0, description="Volume warning threshold")


class CapitalProtectionConfig(BaseModel):
    """Capital protection rules - cannot be overridden."""
    MAX_POSITION_SIZE: float = Field(default=0.05, description="5% max position size")
    DAILY_LOSS_LIMIT: float = Field(default=0.10, description="10% daily loss limit")
    DRAWDOWN_PAUSE: float = Field(default=0.20, description="20% drawdown triggers pause")
    MIN_CONFIDENCE: float = Field(default=0.70, description="70% minimum confidence")


class AgentConfig(BaseModel):
    """Multi-agent system configuration."""
    debate_rounds: int = Field(default=3, description="Number of debate rounds")
    consensus_threshold: float = Field(default=0.70, description="70% consensus required")
    min_agents_for_trade: int = Field(default=3, description="Minimum agents to agree")


class ExecutionConfig(BaseModel):
    """Execution mode configuration."""
    mode: str = Field(default="signal", description="signal or autonomous")
    default_slippage: float = Field(default=0.01, description="1% default slippage")
    max_slippage: float = Field(default=0.05, description="5% max slippage")
    jupiter_api_url: str = Field(default="https://api.jup.ag")


class Settings(BaseSettings):
    """Main settings class."""
    
    # API Configuration
    api: APIConfig = Field(default_factory=APIConfig)
    
    # Filter Configuration
    filters: FilterConfig = Field(default_factory=FilterConfig)
    
    # Capital Protection (immutable)
    capital_protection: CapitalProtectionConfig = Field(
        default_factory=CapitalProtectionConfig
    )
    
    # Agent Configuration
    agents: AgentConfig = Field(default_factory=AgentConfig)
    
    # Execution Configuration
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    
    # Environment
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Database
    data_dir: Path = Field(default_factory=lambda: Path("./data"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def init_settings(**kwargs) -> Settings:
    """Initialize settings with overrides."""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings