"""Jupiter DEX aggregator integration."""

from dataclasses import dataclass
from typing import Optional
import httpx

from memecoin_trader.backend.core.config import settings
from memecoin_trader.backend.core.exceptions import JupiterError
from memecoin_trader.backend.core.logging import main_logger


@dataclass
class SwapQuote:
    """Quote from Jupiter."""
    in_amount: float
    out_amount: float
    price_impact: float
    route: list[dict]
    slippage: float
    
    @property
    def price(self) -> float:
        return self.out_amount / self.in_amount if self.in_amount > 0 else 0


@dataclass
class SwapResult:
    """Result of a swap."""
    success: bool
    transaction: str
    signature: Optional[str] = None
    error: Optional[str] = None


class JupiterClient:
    """Jupiter DEX aggregator client."""
    
    BASE_URL = "https://api.jup.ag"
    
    def __init__(
        self,
        api_url: str = None,
        timeout: float = 30.0
    ):
        self.api_url = api_url or settings.execution.jupiter_api_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=10)
            )
        return self._client
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: float,
        slippage: float = None
    ) -> SwapQuote:
        """Get a quote for a swap.
        
        Args:
            input_mint: Input token mint address (e.g., SOL)
            output_mint: Output token mint address
            amount: Amount to swap (in lamports/smallest unit)
            slippage: Max slippage percentage
            
        Returns:
            SwapQuote with price and route
        """
        slippage = slippage or settings.execution.default_slippage
        
        client = await self._get_client()
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": int(amount),
            "slippageBps": int(slippage * 10000),
            "restrictMode": "strict"
        }
        
        try:
            response = await client.get(
                f"{self.api_url}/quote",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            return SwapQuote(
                in_amount=amount,
                out_amount=data.get("outAmount", 0),
                price_impact=data.get("priceImpactPct", 0),
                route=data.get("route", []),
                slippage=slippage
            )
        
        except httpx.HTTPError as e:
            raise JupiterError(f"Failed to get quote: {e}")
    
    async def get_swap_transaction(
        self,
        quote: SwapQuote,
        user_address: str,
        priority_fee: float = 0.001
    ) -> str:
        """Get swap transaction from quote.
        
        Args:
            quote: Quote from get_quote
            user_address: User's wallet address
            priority_fee: Priority fee in SOL
            
        Returns:
            Transaction as base58 string
        """
        client = await self._get_client()
        
        body = {
            "quoteResponse": {
                "inAmount": str(quote.in_amount),
                "outAmount": str(quote.out_amount),
                "priceImpactPct": str(quote.price_impact),
                "route": quote.route
            },
            "userPublicKey": user_address,
            "prioritizationFeeLamports": int(priority_fee * 1e9),
            "useVersionedTransaction": True
        }
        
        try:
            response = await client.post(
                f"{self.api_url}/swap",
                json=body
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("swapTransaction", "")
        
        except httpx.HTTPError as e:
            raise JupiterError(f"Failed to get swap transaction: {e}")
    
    async def execute_swap(
        self,
        user_address: str,
        user_private_key: str,
        input_token: str,
        output_token: str,
        amount: float,
        slippage: float = None
    ) -> SwapResult:
        """Execute a swap.
        
        Args:
            user_address: User's wallet address
            user_private_key: User's private key (for signing)
            input_token: Input token mint
            output_token: Output token mint
            amount: Amount to swap
            slippage: Max slippage
            
        Returns:
            SwapResult with transaction
        """
        slippage = slippage or settings.execution.default_slippage
        
        # Check slippage tolerance
        max_slippage = settings.execution.max_slippage
        
        try:
            # Get quote
            quote = await self.get_quote(
                input_token,
                output_token,
                amount,
                slippage
            )
            
            # Check price impact
            if quote.price_impact > max_slippage:
                return SwapResult(
                    success=False,
                    transaction="",
                    error=f"Price impact {quote.price_impact:.2%} exceeds max {max_slippage:.2%}"
                )
            
            # Get transaction
            tx = await self.get_swap_transaction(
                quote,
                user_address
            )
            
            # In production, sign with wallet
            # For now, return the transaction
            return SwapResult(
                success=True,
                transaction=tx
            )
        
        except Exception as e:
            return SwapResult(
                success=False,
                transaction="",
                error=str(e)
            )
    
    async def get_tokens(self, limit: int = 100) -> list:
        """Get available tokens on Jupiter."""
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.api_url}/tokens",
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json().get("data", [])
        
        except httpx.HTTPError as e:
            raise JupiterError(f"Failed to get tokens: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Token addresses
SOL_ADDRESS = "So11111111111111111111111111111111111111112"  # Wrapped SOL
USDC_ADDRESS = "EPjFWdd5AufqSSuqol2Kr56H7wdj62uSG9u9JRM5zqc2B"  # USDC

# Singleton instance
_jupiter_client: Optional[JupiterClient] = None


def get_jupiter_client() -> JupiterClient:
    """Get the global Jupiter client instance."""
    global _jupiter_client
    if _jupiter_client is None:
        _jupiter_client = JupiterClient()
    return _jupiter_client