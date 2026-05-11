"""Pump.fun API client for new token mints."""

import asyncio
from typing import Optional, Any
import httpx

from memecoin_trader.backend.core.config import settings
from memecoin_trader.backend.core.exceptions import APIError
from memecoin_trader.backend.core.logging import main_logger


class PumpFunClient:
    """Pump.fun API client for new token mints."""
    
    BASE_URL = "https://api.pump.fun"
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=10)
            )
        return self._client
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        body: dict = None
    ) -> dict:
        """Make an API request."""
        client = await self._get_client()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=body, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                result = response.json()
                
                return result.get("data", result)
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise APIError(f"Pump.fun request failed: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise APIError("Unexpected error in Pump.fun request")
    
    async def get_recent_tokens(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """Get recently created tokens on pump.fun."""
        return await self._request(
            "GET",
            "/v1/tokens/recent",
            params={"limit": limit, "offset": offset}
        )
    
    async def get_token_data(self, token_address: str) -> dict:
        """Get detailed token data from pump.fun."""
        return await self._request(
            "GET",
            f"/v1/tokens/{token_address}"
        )
    
    async def get_token_bonding_curve(self, token_address: str) -> dict:
        """Get bonding curve state for a token."""
        return await self._request(
            "GET",
            f"/v1/tokens/{token_address}/bonding_curve"
        )
    
    async def get_coin_info(self, token_address: str) -> dict:
        """Get complete coin information."""
        return await self._request(
            "GET",
            f"/v1/coins/{token_address}"
        )
    
    async def get_token_market_cap(self, token_address: str) -> dict:
        """Get market cap for a token."""
        return await self._request(
            "GET",
            f"/v1/tokens/{token_address}/market_cap"
        )
    
    async def search_tokens(
        self,
        query: str,
        limit: int = 20
    ) -> list:
        """Search for tokens."""
        return await self._request(
            "GET",
            "/v1/search",
            params={"q": query, "limit": limit}
        )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_pumpfun_client: Optional[PumpFunClient] = None


def get_pumpfun_client() -> PumpFunClient:
    """Get the global Pump.fun client instance."""
    global _pumpfun_client
    if _pumpfun_client is None:
        _pumpfun_client = PumpFunClient()
    return _pumpfun_client