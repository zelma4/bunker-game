"""Test game endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_game():
    """Test creating a new game"""
    response = client.post("/api/games/create", json={"player_name": "Test Player"})
    assert response.status_code == 201
    data = response.json()
    assert "code" in data
    assert len(data["code"]) == 6
    assert data["player_count"] == 1
    assert data["phase"] == "lobby"


def test_join_game():
    """Test joining an existing game"""
    # Create a game first
    create_response = client.post("/api/games/create", json={"player_name": "Host"})
    game_code = create_response.json()["code"]

    # Join the game
    join_response = client.post(
        "/api/games/join", json={"code": game_code, "player_name": "Player 2"}
    )
    assert join_response.status_code == 200
    data = join_response.json()
    assert data["code"] == game_code
    assert data["player_count"] == 2


def test_join_nonexistent_game():
    """Test joining a game that doesn't exist"""
    response = client.post(
        "/api/games/join", json={"code": "NOTEXIST", "player_name": "Player"}
    )
    assert response.status_code == 404


def test_get_game():
    """Test getting game details"""
    # Create a game
    create_response = client.post("/api/games/create", json={"player_name": "Host"})
    game_code = create_response.json()["code"]

    # Get game details
    get_response = client.get(f"/api/games/{game_code}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["code"] == game_code


def test_start_game_minimum_players():
    """Test that game requires minimum players to start"""
    # Create game with only 1 player
    create_response = client.post("/api/games/create", json={"player_name": "Host"})
    game_id = 1  # Assuming first game

    # Try to start with insufficient players
    start_response = client.post(f"/api/games/{game_id}/start")
    assert start_response.status_code == 400


# Cleanup
import os

if os.path.exists("./test.db"):
    os.remove("./test.db")
