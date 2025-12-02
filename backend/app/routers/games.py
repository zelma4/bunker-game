"""Game API routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import secrets

from ..database import get_db
from ..schemas import (
    GameCreate,
    GameResponse,
    GameJoin,
    PlayerResponse,
    VoteRequest,
    CharacterTraits,
    RevealCardRequest,
    UseSpecialRequest,
)
from ..models import Game, Player, GamePhase, PlayerStatus
from ..services import GameService

router = APIRouter(prefix="/api/games", tags=["games"])


def get_session_id(request: Request) -> str:
    """Get or create session ID from cookies"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        print("DEBUG: No session_id cookie found, generating new one")
        session_id = secrets.token_urlsafe(32)
    else:
        print(f"DEBUG: Found session_id cookie: {session_id[:10]}...")
    return session_id


@router.post(
    "/create", response_model=GameResponse, status_code=status.HTTP_201_CREATED
)
async def create_game(
    game_data: GameCreate, request: Request, db: Session = Depends(get_db)
):
    """Create a new game lobby"""
    session_id = get_session_id(request)

    game, player = GameService.create_game(
        db, game_data.player_name, session_id, mode=game_data.mode, goal=game_data.goal
    )

    # Prepare response
    player_response = PlayerResponse.model_validate(player)
    player_response.is_me = True

    response_data = GameResponse(
        id=game.id,
        code=game.code,
        phase=game.phase,
        current_round=game.current_round,
        phase_end_time=game.phase_end_time,
        player_count=1,
        players=[player_response],
        mode=game.mode,
        goal=game.goal,
        catastrophe=game.catastrophe,
        bunker_cards=game.bunker_cards,
        revealed_bunker_cards=game.revealed_bunker_cards,
    )

    return response_data


@router.post("/join", response_model=GameResponse)
async def join_game(
    join_data: GameJoin, request: Request, db: Session = Depends(get_db)
):
    """Join an existing game"""
    session_id = get_session_id(request)

    game, player = GameService.join_game(
        db, join_data.code, join_data.player_name, session_id
    )

    if not game or not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found or cannot join",
        )

    # Get all players
    players = db.query(Player).filter(Player.game_id == game.id).all()

    player_responses = []
    for p in players:
        p_resp = PlayerResponse.model_validate(p)
        is_me = p.session_id == session_id
        p_resp.is_me = is_me

        # Ensure revealed_cards is a list
        revealed = p.revealed_cards if p.revealed_cards else []

        if not is_me and p.status == PlayerStatus.PLAYING:
            # Hide unrevealed cards
            if "profession" not in revealed:
                p_resp.profession = None
            if "biology" not in revealed:
                p_resp.biology = None
            if "health" not in revealed:
                p_resp.health = None
            if "hobby" not in revealed:
                p_resp.hobby = None
            if "baggage" not in revealed:
                p_resp.baggage = None
            if "fact" not in revealed:
                p_resp.fact = None
            p_resp.special_condition = None
            p_resp.threat_card = None

        player_responses.append(p_resp)

    response_data = GameResponse(
        id=game.id,
        code=game.code,
        phase=game.phase,
        current_round=game.current_round,
        phase_end_time=game.phase_end_time,
        player_count=len(players),
        players=player_responses,
        mode=game.mode,
        goal=game.goal,
        catastrophe=game.catastrophe,
        bunker_cards=game.bunker_cards,
        revealed_bunker_cards=game.revealed_bunker_cards,
    )

    # Broadcast player joined via WebSocket
    from ..websockets.connection_manager import manager
    await manager.send_player_joined(game.id, player.name)

    return response_data


@router.get("/{game_code}", response_model=GameResponse)
async def get_game(game_code: str, request: Request, db: Session = Depends(get_db)):
    """Get game details by code"""
    session_id = get_session_id(request)
    game = db.query(Game).filter(Game.code == game_code.upper()).first()

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )

    players = db.query(Player).filter(Player.game_id == game.id).all()

    player_responses = []
    for p in players:
        p_resp = PlayerResponse.model_validate(p)
        is_me = p.session_id == session_id
        p_resp.is_me = is_me
        
        # Always ensure revealed_cards is a list (not None)
        p_resp.revealed_cards = p.revealed_cards if p.revealed_cards else []
        revealed = p_resp.revealed_cards

        if not is_me and p.status == PlayerStatus.PLAYING:
            # Hide unrevealed cards
            if "profession" not in revealed:
                p_resp.profession = None
            if "biology" not in revealed:
                p_resp.biology = None
            if "health" not in revealed:
                p_resp.health = None
            if "hobby" not in revealed:
                p_resp.hobby = None
            if "baggage" not in revealed:
                p_resp.baggage = None
            if "fact" not in revealed:
                p_resp.fact = None
            p_resp.special_condition = None
            p_resp.threat_card = None

        player_responses.append(p_resp)

    response_data = GameResponse(
        id=game.id,
        code=game.code,
        phase=game.phase,
        current_round=game.current_round,
        phase_end_time=game.phase_end_time,
        player_count=len(players),
        players=player_responses,
        mode=game.mode,
        goal=game.goal,
        catastrophe=game.catastrophe,
        bunker_cards=game.bunker_cards,
        revealed_bunker_cards=game.revealed_bunker_cards,
    )

    return response_data


@router.post("/{game_id}/start")
async def start_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    """Start the game (host only)"""
    session_id = get_session_id(request)

    # Verify host
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )

    host = db.query(Player).filter(Player.id == game.host_id).first()

    # Debug logging
    print(f"DEBUG: start_game game_id={game_id} session_id={session_id}")
    if host:
        print(f"DEBUG: host_id={host.id} host_session_id={host.session_id}")
    else:
        print("DEBUG: Host not found")

    if not host or host.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only host can start game"
        )

    success = GameService.start_game(db, game_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start game (not enough players or already started)",
        )

    # Refresh game to get updated data
    db.refresh(game)

    # Log phase and timer info
    print(f"DEBUG: Game started - phase={game.phase.value}, phase_end_time={game.phase_end_time}")

    # Broadcast game started via WebSocket
    from ..websockets.connection_manager import manager

    await manager.send_phase_change(
        game_id,
        game.phase.value,
        game.phase_end_time.isoformat() + 'Z' if game.phase_end_time else None,
        game.current_round,
    )

    return {"message": "Game started successfully"}


@router.post("/{game_id}/vote")
async def vote(
    game_id: int,
    vote_data: VoteRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Vote to eliminate a player"""
    session_id = get_session_id(request)

    # Get voter
    voter = (
        db.query(Player)
        .filter(Player.game_id == game_id, Player.session_id == session_id)
        .first()
    )

    if not voter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )

    success = GameService.vote_player(db, game_id, voter.id, vote_data.target_player_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot vote now or already voted",
        )

    # Broadcast vote update via WebSocket
    from ..websockets.connection_manager import manager
    
    # Get updated vote counts
    players = db.query(Player).filter(Player.game_id == game_id).all()
    votes = {
        p.id: {
            "name": p.name,
            "votes_received": p.votes_received,
            "has_voted": p.has_voted
        }
        for p in players
    }
    
    await manager.send_vote_update(game_id, votes)

    return {"message": "Vote registered"}


# Rate limiting for phase advancement
_last_phase_advance = {}  # game_id -> datetime

@router.post("/{game_id}/advance-phase")
async def advance_phase(game_id: int, db: Session = Depends(get_db)):
    """Advance to next game phase (called by timer or host)"""
    global _last_phase_advance
    
    # Rate limiting: prevent calling within 1 second of last call
    now = datetime.utcnow()
    last_call = _last_phase_advance.get(game_id)
    if last_call and (now - last_call).total_seconds() < 1:
        print(f"DEBUG: Ignoring duplicate advance_phase call for game {game_id}")
        return {"message": "Rate limited", "phase": "unchanged"}
    
    _last_phase_advance[game_id] = now
    
    result = GameService.advance_phase(db, game_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )

    # Get updated game info
    game = db.query(Game).filter(Game.id == game_id).first()

    # Broadcast phase change via WebSocket
    from ..websockets.connection_manager import manager

    # Send elimination notification first (if any)
    if result.get("eliminated_player"):
        eliminated = result["eliminated_player"]
        await manager.send_player_eliminated(
            game_id,
            eliminated["id"],
            eliminated["name"],
            eliminated["revealed_cards"]
        )

    await manager.send_phase_change(
        game_id,
        game.phase.value,
        game.phase_end_time.isoformat() + 'Z' if game.phase_end_time else None,
        game.current_round,
    )

    # Also broadcast bunker card if it was revealed
    if game.phase == GamePhase.CARD_REVEAL:
        await manager.send_bunker_card_revealed(game_id, game.revealed_bunker_cards)

    return {"phase": result["phase"].value if hasattr(result["phase"], 'value') else result["phase"]}


@router.get("/{game_id}/my-character", response_model=CharacterTraits)
async def get_my_character(
    game_id: int, request: Request, db: Session = Depends(get_db)
):
    """Get current player's character traits"""
    session_id = get_session_id(request)

    player = (
        db.query(Player)
        .filter(Player.game_id == game_id, Player.session_id == session_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )

    if not player.profession:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Game not started yet"
        )

    return CharacterTraits(
        profession=player.profession,
        biology=player.biology,
        health=player.health,
        hobby=player.hobby,
        baggage=player.baggage,
        fact=player.fact,
        special_condition=player.special_condition,
        revealed_cards=player.revealed_cards or [],
    )


@router.post("/{game_id}/ready")
async def toggle_ready(game_id: int, request: Request, db: Session = Depends(get_db)):
    """Toggle player ready status"""
    session_id = get_session_id(request)

    player = (
        db.query(Player)
        .filter(Player.game_id == game_id, Player.session_id == session_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )

    from ..models import PlayerStatus

    player.status = (
        PlayerStatus.READY
        if player.status == PlayerStatus.WAITING
        else PlayerStatus.WAITING
    )

    db.commit()

    return {"status": player.status}


@router.post("/{game_id}/reveal-card")
async def reveal_card(
    game_id: int,
    card_data: RevealCardRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Reveal a player's card"""
    session_id = get_session_id(request)

    # Get player
    player = (
        db.query(Player)
        .filter(Player.game_id == game_id, Player.session_id == session_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )

    success = GameService.reveal_player_card(
        db, game_id, player.id, card_data.card_type
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reveal this card"
        )

    # Get card value to broadcast
    card_value = getattr(player, card_data.card_type, None)

    # Broadcast to other players
    from ..websockets.connection_manager import manager

    await manager.send_player_revealed_card(
        game_id, player.id, player.name, card_data.card_type, card_value
    )

    return {"message": "Card revealed", "card_type": card_data.card_type}


@router.post("/{game_id}/use-special")
async def use_special_condition(
    game_id: int,
    special_data: UseSpecialRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Use player's special condition"""
    session_id = get_session_id(request)

    # Get player
    player = (
        db.query(Player)
        .filter(Player.game_id == game_id, Player.session_id == session_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )

    if not player.special_condition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No special condition"
        )

    if player.special_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Special condition already used"
        )

    # Execute special condition
    from ..services.special_conditions import SpecialConditionHandler

    params = special_data.dict(exclude_unset=True)
    result = SpecialConditionHandler.execute(db, game_id, player.id, params)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to use special condition")
        )

    # Broadcast to other players
    from ..websockets.connection_manager import manager

    await manager.send_special_card_used(
        game_id, 
        player.name, 
        player.special_condition.get("name")
    )

    # Refresh player to get updated data
    db.refresh(player)

    return {
        "message": result.get("message"),
        "effect": result.get("effect"),
        "data": {k: v for k, v in result.items() if k not in ["success", "message", "effect"]}
    }

