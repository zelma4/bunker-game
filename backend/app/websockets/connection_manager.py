"""WebSocket connection manager"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time game updates"""

    def __init__(self):
        # game_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # websocket -> game_id
        self.connection_game_map: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, game_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if game_id not in self.active_connections:
            self.active_connections[game_id] = []

        self.active_connections[game_id].append(websocket)
        self.connection_game_map[websocket] = game_id

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_game_map:
            game_id = self.connection_game_map[websocket]

            if game_id in self.active_connections:
                self.active_connections[game_id].remove(websocket)

                # Clean up empty game rooms
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]

            del self.connection_game_map[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_json(
                {**message, "timestamp": datetime.utcnow().isoformat()}
            )
        except:
            pass

    async def broadcast_to_game(
        self, game_id: int, message: dict, exclude: WebSocket = None
    ):
        """Broadcast a message to all connections in a game"""
        if game_id not in self.active_connections:
            return

        message_data = {**message, "timestamp": datetime.utcnow().isoformat()}

        disconnected = []

        for connection in self.active_connections[game_id]:
            if connection == exclude:
                continue

            try:
                await connection.send_json(message_data)
            except:
                disconnected.append(connection)

        # Clean up disconnected sockets
        for conn in disconnected:
            self.disconnect(conn)

    async def send_game_update(self, game_id: int, data: dict):
        """Send a game state update to all players"""
        await self.broadcast_to_game(game_id, {"type": "game_update", "data": data})

    async def send_chat_message(self, game_id: int, player_name: str, message: str):
        """Broadcast a chat message"""
        await self.broadcast_to_game(
            game_id,
            {"type": "chat", "data": {"player_name": player_name, "message": message}},
        )

    async def send_player_joined(self, game_id: int, player_name: str):
        """Notify that a player joined"""
        await self.broadcast_to_game(
            game_id, {"type": "player_joined", "data": {"player_name": player_name}}
        )

    async def send_player_left(self, game_id: int, player_name: str):
        """Notify that a player left"""
        await self.broadcast_to_game(
            game_id, {"type": "player_left", "data": {"player_name": player_name}}
        )

    async def send_phase_change(
        self, game_id: int, phase: str, phase_end_time: str = None, current_round: int = None
    ):
        """Notify about phase change"""
        print(f"DEBUG: Broadcasting phase_change to game {game_id}: phase={phase}, phase_end_time={phase_end_time}, current_round={current_round}")
        await self.broadcast_to_game(
            game_id,
            {
                "type": "phase_change",
                "data": {
                    "phase": phase,
                    "phase_end_time": phase_end_time,
                    "current_round": current_round
                },
            },
        )

    async def send_vote_update(self, game_id: int, votes: dict):
        """Send vote count update"""
        await self.broadcast_to_game(game_id, {"type": "vote_update", "data": votes})

    async def send_bunker_card_revealed(self, game_id: int, revealed_count: int):
        """Notify that a bunker card was revealed"""
        await self.broadcast_to_game(
            game_id,
            {
                "type": "bunker_card_revealed",
                "data": {"revealed_count": revealed_count},
            },
        )

    async def send_player_revealed_card(
        self,
        game_id: int,
        player_id: int,
        player_name: str,
        card_type: str,
        card_value: str = None,
    ):
        """Notify that a player revealed a card"""
        await self.broadcast_to_game(
            game_id,
            {
                "type": "player_revealed_card",
                "data": {
                    "player_id": player_id,
                    "player_name": player_name,
                    "card_type": card_type,
                    "card_value": card_value,
                },
            },
        )

    async def send_special_card_used(
        self, game_id: int, player_name: str, special_name: str
    ):
        """Notify that a player used their special condition"""
        await self.broadcast_to_game(
            game_id,
            {
                "type": "special_card_used",
                "data": {"player_name": player_name, "special_name": special_name},
            },
        )

    async def send_player_eliminated(
        self, game_id: int, player_id: int, player_name: str, revealed_cards: list
    ):
        """Notify that a player was eliminated"""
        await self.broadcast_to_game(
            game_id,
            {
                "type": "player_eliminated",
                "data": {
                    "player_id": player_id,
                    "player_name": player_name,
                    "revealed_cards": revealed_cards,
                },
            },
        )


# Global connection manager instance
manager = ConnectionManager()
