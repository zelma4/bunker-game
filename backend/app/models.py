"""Database models for Bunker Game"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import secrets

Base = declarative_base()


class GamePhase(str, Enum):
    """Game phase enumeration"""
    LOBBY = "lobby"
    BUNKER_REVEAL = "bunker_reveal"  # Відкривання картки бункера
    CARD_REVEAL = "card_reveal"      # Відкривання карток гравців
    DISCUSSION = "discussion"
    VOTING = "voting"
    REVEAL = "reveal"
    SURVIVAL_CHECK = "survival_check"  # Для режиму Історія виживання
    ENDED = "ended"


class PlayerStatus(str, Enum):
    """Player status enumeration"""
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    ELIMINATED = "eliminated"
    SURVIVED = "survived"
    DEAD = "dead"  # Для режиму Історія виживання


class GameMode(str, Enum):
    """Game mode enumeration"""
    BASIC = "basic"  # Базовий режим
    SURVIVAL_STORY = "survival_story"  # Історія виживання


class GameGoal(str, Enum):
    """Game goal enumeration"""
    SALVATION = "salvation"  # Порятунок (до 7 гравців)
    REBIRTH = "rebirth"  # Відродження (8+ гравців, потрібна пара)


class Game(Base):
    """Game lobby/session model"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(6), unique=True, index=True, nullable=False)
    host_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    phase = Column(SQLEnum(GamePhase), default=GamePhase.LOBBY, nullable=False)
    current_round = Column(Integer, default=0)
    phase_end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Режим та ціль гри
    mode = Column(SQLEnum(GameMode), default=GameMode.BASIC, nullable=False)
    goal = Column(SQLEnum(GameGoal), default=GameGoal.SALVATION, nullable=False)
    
    # Картка катастрофи та бункера
    catastrophe = Column(JSON, nullable=True)  # {name, description, duration}
    bunker_cards = Column(JSON, nullable=True)  # Список з 5 карток
    revealed_bunker_cards = Column(Integer, default=0)  # Скільки відкрито
    
    # Relationships
    players = relationship("Player", back_populates="game", foreign_keys="Player.game_id")
    messages = relationship("ChatMessage", back_populates="game", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_code() -> str:
        """Generate unique 6-character room code"""
        return secrets.token_urlsafe(4)[:6].upper()


class Player(Base):
    """Player model"""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    status = Column(SQLEnum(PlayerStatus), default=PlayerStatus.WAITING, nullable=False)
    is_host = Column(Boolean, default=False)
    
    # 6 типів карток персонажа
    profession = Column(String(100), nullable=True)
    biology = Column(String(100), nullable=True)  # "Чоловік, 35 років"
    health = Column(String(100), nullable=True)
    hobby = Column(String(100), nullable=True)
    baggage = Column(String(200), nullable=True)  # Багаж
    fact = Column(String(200), nullable=True)  # Факт
    
    # Особлива умова
    special_condition = Column(JSON, nullable=True)  # {name, description}
    special_used = Column(Boolean, default=False)
    
    # Відкриті картки (для покрокового відкривання)
    revealed_cards = Column(JSON, default=lambda: [])  # ["profession", "health", ...]
    
    # Картка загрози (для режиму Історія виживання)
    threat_card = Column(JSON, nullable=True)  # {name, description, solution}
    
    # Voting
    votes_received = Column(Integer, default=0)
    has_voted = Column(Boolean, default=False)
    voted_for = Column(Integer, nullable=True)  # ID гравця, за якого проголосував
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="players", foreign_keys=[game_id])
    messages = relationship("ChatMessage", back_populates="player", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="messages")
    player = relationship("Player", back_populates="messages")
