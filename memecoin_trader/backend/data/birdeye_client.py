"""Birdeye API client for token data."""

from typing import Optional, Any
import httpx

from memecoin_trader.backend.core.config import settings
from memecoin_trader.backend.core.exceptions import BirdeyeError
from memecoin_trader.backend.core.logging import main_logger


class BirdeyeClient:
    """Birdeye API client for real-time token data."""
    
    BASE_URL = "https://api.birdeye.io"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.api_key = api_key or settings.api.birdeye_api_key
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
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
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
                
                if result.get("success") is False:
                    raise BirdeyeError(f"Birdeye API error: {result.get('message')}")
                
                return result.get("data", result)
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise BirdeyeError(f"Birdeye request failed: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise BirdeyeError("Unexpected error in Birdeye request")
    
    async def get_token_price(self, token_address: str) -> dict:
        """Get current token price."""
        return await self._request(
            "GET",
            f"/defi/token/price",
            params={"address": token_address}
        )
    
    async def get_token_metadata(self, token_address: str) -> dict:
        """Get token metadata."""
        return await self._request(
            "GET",
            f"/defi/token/meta",
            params={"address": token_address}
        )
    
    async def get_token_list(
        self,
        sort_by: str = "volume24h",
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """Get token list sorted by volume."""
        return await self._request(
            "GET",
            "/defi/tokenlist",
            params={
                "sort": sort_by,
                "limit": limit,
                "offset": offset
            }
        )
    
    async def get_token_trades(
        self,
        token_address: str,
        limit: int = 50
    ) -> list:
        """Get recent token trades."""
        return await self._request(
            "GET",
            f"/defi/token/{token_address}/trades",
            params={"limit": limit}
        )
    
    async def get_token_history(
        self,
        token_address: str,
        time_from: int,
        time_to: int
    ) -> list:
        """Get token price history."""
        return await self._request(
            "GET",
            f"/defi/token/{token_address}/history",
            params={
                "time_from": time_from,
                "time_to": time_to
            }
        )
    
    async def get_token_liquidity(self, token_address: str) -> dict:
        """Get token liquidity pools."""
        return await self._request(
            "GET",
            f"/defi/token/{token_address}/liquidity"
        )
    
    async def get_multiple_prices(self, addresses: list) -> dict:
        """Get prices for multiple tokens."""
        return await self._request(
            "POST",
            "/defi/multi_price",
            body={"addresses": addresses}
        )
    
    async def search_token(self, query: str) -> list:
        """Search for tokens."""
        return await self._request(
            "GET",
            "/defi/search",
            params={"q": query}
        )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


import asyncio

# Singleton instance
_birdeye_client: Optional[BirdeyeClient] = None


def get_birdeye_client() -> BirdeyeClient:
    """Get the global Birdeye client instance."""
    global _birdeye_client
    if _birdeye_client is None:
        _birdeye_client = BirdeyeClient()
    return _birdeye_client