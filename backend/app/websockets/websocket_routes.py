"""WebSocket routes for real-time communication"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json

from ..database import get_db
from ..models import Game, Player
from .connection_manager import manager

router = APIRouter()


@router.websocket("/ws/{game_code}")
async def websocket_endpoint(
    websocket: WebSocket, game_code: str, db: Session = Depends(get_db)
):
    """WebSocket endpoint for game real-time updates"""

    # Find game
    game = db.query(Game).filter(Game.code == game_code.upper()).first()

    if not game:
        await websocket.close(code=1008)  # Policy violation
        return

    # Connect
    await manager.connect(websocket, game.id)

    try:
        while True:
            # Receive messages
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle different message types
            msg_type = message_data.get("type")

            if msg_type == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

            elif msg_type == "chat":
                # Broadcast chat message
                await manager.send_chat_message(
                    game.id,
                    message_data.get("player_name", "Unknown"),
                    message_data.get("message", ""),
                )

            elif msg_type == "pause_toggle":
                # Broadcast pause state to all players
                paused = message_data.get("paused", False)
                await manager.broadcast_to_game(
                    game.id, {"type": "timer_paused", "data": {"paused": paused}}
                )

            elif msg_type == "request_update":
                # Send current game state
                players = db.query(Player).filter(Player.game_id == game.id).all()

                game_state = {
                    "phase": game.phase.value,
                    "current_round": game.current_round,
                    "phase_end_time": game.phase_end_time.isoformat() + "Z"
                    if game.phase_end_time
                    else None,
                    "players": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "status": p.status.value,
                            "is_host": p.is_host,
                            "votes_received": p.votes_received,
                            "has_voted": p.has_voted,
                            "revealed_cards": p.revealed_cards
                            if p.revealed_cards
                            else [],
                        }
                        for p in players
                    ],
                }

                await manager.send_personal_message(
                    {"type": "game_update", "data": game_state}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
