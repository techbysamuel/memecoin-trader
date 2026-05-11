"""WebSocket listener for Solana events."""

import asyncio
import json
from typing import Optional, Callable, Any
import websockets

from memecoin_trader.backend.core.logging import main_logger


class WebSocketListener:
    """WebSocket listener for Solana events."""
    
    def __init__(
        self,
        rpc_ws_url: Optional[str] = None,
        on_token_update: Optional[Callable] = None,
        on_new_token: Optional[Callable] = None,
        on_trade: Optional[Callable] = None
    ):
        self.rpc_ws_url = rpc_ws_url or "wss://api.mainnet-beta.solana.com"
        self.on_token_update = on_token_update
        self.on_new_token = on_new_token
        self.on_trade = on_trade
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._subscriptions: dict[int, str] = {}
    
    async def connect(self):
        """Connect to WebSocket."""
        self._ws = await websockets.connect(self.rpc_ws_url)
        self._running = True
    
    async def subscribe_new_tokens(self):
        """Subscribe to new token mints."""
        if not self._ws:
            await self.connect()
        
        subscribe_id = 1
        await self._ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": subscribe_id,
            "method": "programSubscribe",
            "params": [
                "TokenkegQfeZyiNwAJbNbG KPFXiAcVw88YDWRdNsU9",  # Token program
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed"
                }
            ]
        }))
        self._subscriptions[subscribe_id] = "new_tokens"
        return subscribe_id
    
    async def subscribe_token_trades(self, token_address: str):
        """Subscribe to trades for a specific token."""
        if not self._ws:
            await self.connect()
        
        subscribe_id = len(self._subscriptions) + 1
        await self._ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": subscribe_id,
            "method": "accountSubscribe",
            "params": [
                token_address,
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed"
                }
            ]
        }))
        self._subscriptions[subscribe_id] = f"trades:{token_address}"
        return subscribe_id
    
    async def unsubscribe(self, subscription_id: int):
        """Unsubscribe from updates."""
        if not self._ws:
            return
        
        await self._ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": subscription_id,
            "method": "unsubscribe",
            "params": [subscription_id]
        }))
        self._subscriptions.pop(subscription_id, None)
    
    async def listen(self):
        """Listen for WebSocket messages."""
        if not self._ws:
            await self.connect()
        
        while self._running:
            try:
                message = await self._ws.recv()
                await self._process_message(json.loads(message))
            except websockets.ConnectionClosed:
                main_logger.warning("WebSocket connection closed, reconnecting...")
                await self.connect()
            except Exception as e:
                main_logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: dict):
        """Process incoming WebSocket message."""
        if "params" not in message:
            return
        
        sub_id = message.get("params", {}).get("subscription", 0)
        sub_type = self._subscriptions.get(sub_id)
        
        if not sub_type:
            return
        
        result = message.get("result", {})
        
        if sub_type == "new_tokens" and self.on_new_token:
            await self.on_new_token(result)
        elif sub_type.startswith("trades:") and self.on_trade:
            token = sub_type.split(":")[1]
            await self.on_trade(token, result)
        elif self.on_token_update:
            await self.on_token_update(result)
    
    async def close(self):
        """Close WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None


# Singleton instance
_ws_listener: Optional[WebSocketListener] = None


def get_ws_listener(
    on_new_token: Optional[Callable] = None,
    on_trade: Optional[Callable] = None
) -> WebSocketListener:
    """Get the global WebSocket listener instance."""
    global _ws_listener
    if _ws_listener is None:
        _ws_listener = WebSocketListener(
            on_new_token=on_new_token,
            on_trade=on_trade
        )
    return _ws_listener