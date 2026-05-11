"""RPC client for Solana blockchain data."""

import asyncio
from typing import Optional, Any
import httpx
from Solders import Pubkey

from memecoin_trader.backend.core.config import settings
from memecoin_trader.backend.core.exceptions import RPCError
from memecoin_trader.backend.core.logging import main_logger


class RPCClient:
    """Helius RPC client for Solana data."""
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        rpc_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.rpc_url = rpc_url or settings.api.helius_rpc_url
        self.rpc_key = rpc_key or settings.api.helius_rpc_key
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
    
    async def _call(self, method: str, params: list = None) -> dict:
        """Make an RPC call with retry logic."""
        client = await self._get_client()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        headers = {"Content-Type": "application/json"}
        if self.rpc_key:
            headers["x-api-key"] = self.rpc_key
        
        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                if "error" in result:
                    raise RPCError(f"RPC error: {result['error']}")
                
                return result.get("result", {})
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise RPCError(f"RPC call failed after {self.max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise RPCError("Unexpected error in RPC call")
    
    async def get_token_data(self, token_address: str) -> dict:
        """Get token account data."""
        return await self._call("getAccountInfo", [
            str(Pubkey.from_string(token_address)),
            {"encoding": "jsonParsed"}
        ])
    
    async def get_token_balance(self, token_address: str, wallet: str) -> dict:
        """Get token balance for a wallet."""
        return await self._call("getTokenAccountBalance", [
            {"pubkey": token_address, "encoding": "jsonParsed"}
        ])
    
    async def get_token_supply(self, token_address: str) -> dict:
        """Get total token supply."""
        return await self._call("getTokenSupply", [token_address])
    
    async def get_holders(self, token_address: str, limit: int = 100) -> list:
        """Get token holders (via getProgramAccounts)."""
        # This is a simplified version - in production you'd use 
        # a dedicated indexer like Helius token list API
        return await self._call("getTokenLargestAccounts", [token_address])
    
    async def get_recent_transactions(
        self,
        token_address: str,
        limit: int = 50
    ) -> list:
        """Get recent transactions for a token."""
        # Using getSignaturesForAddress
        return await self._call("getSignaturesForAddress", [
            str(Pubkey.from_string(token_address)),
            {"limit": limit}
        ])
    
    async def get_transaction(self, signature: str) -> dict:
        """Get a specific transaction."""
        return await self._call("getTransaction", [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
        ])
    
    async def get_cluster_nodes(self) -> list:
        """Get all cluster nodes."""
        return await self._call("getClusterNodes")
    
    async def get_slot(self) -> int:
        """Get current slot."""
        return await self._call("getSlot")
    
    async def get_block_time(self, slot: int) -> int:
        """Get block time for a slot."""
        return await self._call("getBlockTime", [slot])
    
    async def get_multiple_accounts(self, addresses: list) -> list:
        """Get multiple accounts at once."""
        return await self._call("getMultipleAccounts", [
            [str(Pubkey.from_string(addr)) for addr in addresses]
        ])
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_rpc_client: Optional[RPCClient] = None


def get_rpc_client() -> RPCClient:
    """Get the global RPC client instance."""
    global _rpc_client
    if _rpc_client is None:
        _rpc_client = RPCClient()
    return _rpc_client