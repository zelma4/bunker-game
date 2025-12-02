"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import GamePhase, PlayerStatus, GameMode, GameGoal


class PlayerCreate(BaseModel):
    """Schema for creating a player"""

    name: str = Field(..., min_length=1, max_length=50)

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class PlayerResponse(BaseModel):
    """Schema for player response"""

    id: int
    name: str
    status: PlayerStatus
    is_host: bool

    # 6 карток персонажа
    profession: Optional[str] = None
    biology: Optional[str] = None
    health: Optional[str] = None
    hobby: Optional[str] = None
    baggage: Optional[str] = None
    fact: Optional[str] = None

    # Особлива умова (приховується від інших)
    special_condition: Optional[Dict[str, Any]] = None
    special_used: bool = False

    # Відкриті картки
    revealed_cards: List[str] = []

    # Картка загрози
    threat_card: Optional[Dict[str, Any]] = None

    # Голосування
    votes_received: int = 0
    has_voted: bool = False
    voted_for: Optional[int] = None

    is_me: bool = False

    class Config:
        from_attributes = True


class GameCreate(BaseModel):
    """Schema for creating a game"""

    player_name: str = Field(..., min_length=1, max_length=50)
    mode: GameMode = GameMode.BASIC
    goal: GameGoal = GameGoal.SALVATION


class GameJoin(BaseModel):
    """Schema for joining a game"""

    code: str = Field(..., min_length=6, max_length=6)
    player_name: str = Field(..., min_length=1, max_length=50)


class GameResponse(BaseModel):
    """Schema for game response"""

    id: int
    code: str
    phase: GamePhase
    current_round: int
    phase_end_time: Optional[str] = None  # Changed to str to include 'Z' suffix
    player_count: int
    players: List[PlayerResponse] = []

    # Режим та ціль
    mode: GameMode
    goal: GameGoal

    # Катастрофа та бункер
    catastrophe: Optional[Dict[str, Any]] = None
    bunker_cards: Optional[List[str]] = None
    revealed_bunker_cards: int = 0

    class Config:
        from_attributes = True

    @validator("phase_end_time", pre=True, always=True)
    def serialize_phase_end_time(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat() + 'Z'
        if isinstance(v, str) and not v.endswith('Z'):
            return v + 'Z'
        return v


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""

    message: str = Field(..., min_length=1, max_length=500)

    @validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""

    id: int
    player_id: int
    player_name: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    """Schema for voting"""

    target_player_id: int


class RevealCardRequest(BaseModel):
    """Schema for revealing a card"""

    card_type: str = Field(
        ..., pattern="^(profession|biology|health|hobby|baggage|fact)$"
    )


class UseSpecialRequest(BaseModel):
    """Schema for using special condition"""
    
    # Optional parameters depending on special type
    target_player_id: Optional[int] = None
    source_player_id: Optional[int] = None
    player1_id: Optional[int] = None
    player2_id: Optional[int] = None
    card_type: Optional[str] = None
    guess: Optional[str] = None


class CharacterTraits(BaseModel):
    """Schema for character traits"""

    profession: Optional[str] = None
    biology: Optional[str] = None
    health: Optional[str] = None
    hobby: Optional[str] = None
    baggage: Optional[str] = None
    fact: Optional[str] = None
    special_condition: Optional[Dict[str, Any]] = None
    revealed_cards: List[str] = []
    threat_card: Optional[Dict[str, Any]] = None


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""

    type: str  # 'chat', 'game_update', 'player_joined', 'player_left', 'vote', 'phase_change'
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
