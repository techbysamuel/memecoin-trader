"""GMGN AI API client for smart money tracking."""

import asyncio
from typing import Optional, Any
import httpx

from memecoin_trader.backend.core.config import settings
from memecoin_trader.backend.core.exceptions import GMGNFError
from memecoin_trader.backend.core.logging import main_logger


class GMGNClient:
    """GMGN AI API client for smart money tracking."""
    
    BASE_URL = "https://api.gmgn.ai"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.api_key = api_key or settings.api.gmgn_api_key
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
            "Authorization": f"Bearer {self.api_key}",
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
                
                return result.get("data", result)
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise GMGNFError(f"GMGN request failed: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise GMGNFError("Unexpected error in GMGN request")
    
    async def get_wallet_profile(self, wallet_address: str) -> dict:
        """Get wallet profile and history."""
        return await self._request(
            "GET",
            f"/v1/wallet/{wallet_address}"
        )
    
    async def get_wallet_tokens(self, wallet_address: str) -> list:
        """Get tokens held by a wallet."""
        return await self._request(
            "GET",
            f"/v1/wallet/{wallet_address}/tokens"
        )
    
    async def get_wallet_pnl(self, wallet_address: str) -> dict:
        """Get wallet PnL summary."""
        return await self._request(
            "GET",
            f"/v1/wallet/{wallet_address}/pnl"
        )
    
    async def get_smart_money_list(
        self,
        min_volume: float = 100_000,
        limit: int = 50
    ) -> list:
        """Get list of smart money wallets."""
        return await self._request(
            "GET",
            "/v1/smartmoney",
            params={"min_volume": min_volume, "limit": limit}
        )
    
    async def get_token_holders(self, token_address: str) -> list:
        """Get top holders of a token."""
        return await self._request(
            "GET",
            f"/v1/token/{token_address}/holders"
        )
    
    async def get_token_traders(self, token_address: str) -> list:
        """Get recent traders for a token."""
        return await self._request(
            "GET",
            f"/v1/token/{token_address}/traders"
        )
    
    async def get_token_copy_traders(
        self,
        token_address: str,
        min_followers: int = 10
    ) -> list:
        """Get wallets copying top traders."""
        return await self._request(
            "GET",
            f"/v1/token/{token_address}/copy_traders",
            params={"min_followers": min_followers}
        )
    
    async def get_token_pool_info(self, token_address: str) -> dict:
        """Get pool information for token."""
        return await self._request(
            "GET",
            f"/v1/token/{token_address}/pool"
        )
    
    async def search_wallets(self, query: str) -> list:
        """Search for wallets."""
        return await self._request(
            "GET",
            "/v1/search/wallets",
            params={"q": query}
        )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_gmgn_client: Optional[GMGNClient] = None


def get_gmgn_client() -> GMGNClient:
    """Get the global GMGN client instance."""
    global _gmgn_client
    if _gmgn_client is None:
        _gmgn_client = GMGNClient()
    return _gmgn_client