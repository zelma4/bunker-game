"""Chat API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..schemas import ChatMessageCreate, ChatMessageResponse
from ..models import ChatMessage, Player
from .games import get_session_id

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple rate limiting storage (in production, use Redis)
rate_limit_storage: dict[str, list[datetime]] = {}


def check_rate_limit(session_id: str, limit: int = 10, window_seconds: int = 60) -> bool:
    """Check if user has exceeded rate limit"""
    now = datetime.utcnow()
    
    if session_id not in rate_limit_storage:
        rate_limit_storage[session_id] = []
    
    # Remove old timestamps
    rate_limit_storage[session_id] = [
        ts for ts in rate_limit_storage[session_id]
        if now - ts < timedelta(seconds=window_seconds)
    ]
    
    # Check limit
    if len(rate_limit_storage[session_id]) >= limit:
        return False
    
    # Add current timestamp
    rate_limit_storage[session_id].append(now)
    return True


@router.post("/{game_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    game_id: int,
    message_data: ChatMessageCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Send a chat message"""
    session_id = get_session_id(request)
    
    # Rate limiting
    if not check_rate_limit(session_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages, please slow down"
        )
    
    # Get player
    player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.session_id == session_id
    ).first()
    
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    
    # Create message
    chat_message = ChatMessage(
        game_id=game_id,
        player_id=player.id,
        message=message_data.message
    )
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    
    # Return response
    return ChatMessageResponse(
        id=chat_message.id,
        player_id=player.id,
        player_name=player.name,
        message=chat_message.message,
        timestamp=chat_message.timestamp
    )


@router.get("/{game_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    game_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent chat messages"""
    messages = db.query(ChatMessage, Player).join(
        Player, ChatMessage.player_id == Player.id
    ).filter(
        ChatMessage.game_id == game_id
    ).order_by(
        ChatMessage.timestamp.desc()
    ).limit(limit).all()
    
    return [
        ChatMessageResponse(
            id=msg.id,
            player_id=msg.player_id,
            player_name=player.name,
            message=msg.message,
            timestamp=msg.timestamp
        )
        for msg, player in messages
    ][::-1]  # Reverse to chronological order
