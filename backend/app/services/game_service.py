"""Game service for business logic"""

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import random
from ..models import Game, Player, GamePhase, PlayerStatus, GameMode, GameGoal
from ..config import settings
from ..card_data import (
    get_random_cards,
    get_random_catastrophe,
    get_random_bunker_cards,
    get_random_threat_cards,
)
from ..game_logic import (
    get_votings_for_round,
    get_bunker_capacity,
    get_mandatory_card_for_round,
    get_phase_duration,
    get_max_rounds,
)


class GameService:
    """Service for game operations"""

    @staticmethod
    def create_game(
        db: Session,
        player_name: str,
        session_id: str,
        mode: GameMode = GameMode.BASIC,
        goal: GameGoal = GameGoal.SALVATION,
    ) -> Tuple[Game, Player]:
        """Create a new game lobby"""
        # Check for existing player with this session_id
        existing_player = (
            db.query(Player).filter(Player.session_id == session_id).first()
        )

        if existing_player:
            # If player was host of another game, clear that
            if existing_player.game_id:
                old_game = (
                    db.query(Game).filter(Game.id == existing_player.game_id).first()
                )
                if old_game and old_game.host_id == existing_player.id:
                    old_game.host_id = None

            player = existing_player
        else:
            player = None

        # Generate unique code
        code = Game.generate_code()
        while db.query(Game).filter(Game.code == code).first():
            code = Game.generate_code()

        # Create game
        game = Game(code=code, mode=mode, goal=goal)
        db.add(game)
        db.flush()  # Get game.id

        if player:
            # Update existing player
            GameService._reset_player(player, game.id, player_name, is_host=True)
        else:
            # Create host player
            player = Player(
                game_id=game.id,
                session_id=session_id,
                name=player_name,
                is_host=True,
                status=PlayerStatus.READY,
                revealed_cards=[],
            )
            db.add(player)

        db.flush()  # Flush player to get player.id

        # Set host_id now that player has an ID
        game.host_id = player.id

        db.commit()
        db.refresh(game)
        db.refresh(player)

        return game, player

    @staticmethod
    def _reset_player(player: Player, game_id: int, name: str, is_host: bool = False):
        """Reset player for a new game"""
        player.game_id = game_id
        player.name = name
        player.is_host = is_host
        player.status = PlayerStatus.READY if is_host else PlayerStatus.WAITING

        # Reset all cards
        player.profession = None
        player.biology = None
        player.health = None
        player.hobby = None
        player.baggage = None
        player.fact = None
        player.special_condition = None
        player.special_used = False
        player.revealed_cards = []
        flag_modified(player, "revealed_cards")
        player.threat_card = None

        # Reset voting
        player.votes_received = 0
        player.has_voted = False
        player.voted_for = None
        player.joined_at = datetime.utcnow()

    @staticmethod
    def join_game(
        db: Session, code: str, player_name: str, session_id: str
    ) -> Tuple[Optional[Game], Optional[Player]]:
        """Join an existing game"""
        game = db.query(Game).filter(Game.code == code.upper()).first()

        if not game:
            return None, None

        # Check if game is in lobby phase
        if game.phase != GamePhase.LOBBY:
            return None, None

        # Check player count
        player_count = db.query(Player).filter(Player.game_id == game.id).count()
        if player_count >= settings.MAX_PLAYERS:
            return None, None

        # Check for existing player with this session_id
        existing_player = (
            db.query(Player).filter(Player.session_id == session_id).first()
        )

        if existing_player:
            # If player was host of another game, clear that
            if existing_player.game_id:
                old_game = (
                    db.query(Game).filter(Game.id == existing_player.game_id).first()
                )
                if old_game and old_game.host_id == existing_player.id:
                    old_game.host_id = None

            player = existing_player
            GameService._reset_player(player, game.id, player_name, is_host=False)
        else:
            # Create player
            player = Player(
                game_id=game.id,
                session_id=session_id,
                name=player_name,
                status=PlayerStatus.WAITING,
                revealed_cards=[],
            )
            db.add(player)

        db.commit()
        db.refresh(player)

        return game, player

    @staticmethod
    def start_game(db: Session, game_id: int) -> bool:
        """Start the game and assign traits"""
        game = db.query(Game).filter(Game.id == game_id).first()

        if not game or game.phase != GamePhase.LOBBY:
            return False

        players = db.query(Player).filter(Player.game_id == game_id).all()

        # Check minimum players
        if len(players) < settings.MIN_PLAYERS:
            return False

        # Assign random traits to each player (6 карток + особлива умова)
        for player in players:
            cards = get_random_cards()
            player.profession = cards["profession"]
            player.biology = cards["biology"]
            player.health = cards["health"]
            player.hobby = cards["hobby"]
            player.baggage = cards["baggage"]
            player.fact = cards["fact"]
            player.special_condition = cards["special_condition"]
            player.status = PlayerStatus.PLAYING
            player.revealed_cards = []  # Всі картки закриті
            flag_modified(player, "revealed_cards")

        # Assign catastrophe and bunker cards
        game.catastrophe = get_random_catastrophe()
        game.bunker_cards = get_random_bunker_cards(5)  # 5 карток бункера
        game.revealed_bunker_cards = 0

        # Update game state
        game.phase = GamePhase.BUNKER_REVEAL  # Почати з відкривання картки бункера
        game.current_round = 1
        game.started_at = datetime.utcnow()

        # Set timer for bunker reveal phase
        duration = get_phase_duration("bunker_reveal")
        game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)

        db.commit()
        return True

    @staticmethod
    def reveal_bunker_card(db: Session, game_id: int) -> bool:
        """Reveal next bunker card"""
        game = db.query(Game).filter(Game.id == game_id).first()

        if not game or not game.bunker_cards:
            return False

        if game.revealed_bunker_cards >= len(game.bunker_cards):
            return False  # All cards already revealed

        game.revealed_bunker_cards += 1
        db.commit()
        return True

    @staticmethod
    def reveal_player_card(
        db: Session, game_id: int, player_id: int, card_type: str
    ) -> bool:
        """Reveal a player's card"""
        player = (
            db.query(Player)
            .filter(Player.game_id == game_id, Player.id == player_id)
            .first()
        )

        if not player:
            return False

        # Check if card type is valid
        valid_cards = ["profession", "biology", "health", "hobby", "baggage", "fact"]
        if card_type not in valid_cards:
            return False

        # Check if card is already revealed
        if card_type in player.revealed_cards:
            return False

        # Check mandatory first round card
        game = db.query(Game).filter(Game.id == game_id).first()
        if game.current_round == 1:
            mandatory = get_mandatory_card_for_round(1)
            if mandatory and card_type != mandatory:
                return False  # Must reveal profession in round 1

        # Reveal the card - use flag_modified for JSON field
        if player.revealed_cards is None:
            player.revealed_cards = []

        player.revealed_cards.append(card_type)
        flag_modified(player, "revealed_cards")  # Important for JSON fields!
        db.commit()
        db.refresh(player)
        return True

    @staticmethod
    def advance_phase(db: Session, game_id: int) -> Optional[dict]:
        """Advance to the next game phase

        Returns:
            dict with 'phase' and optionally 'eliminated_player' info
        """
        game = db.query(Game).filter(Game.id == game_id).first()

        if not game:
            return None

        players = (
            db.query(Player)
            .filter(Player.game_id == game_id, Player.status == PlayerStatus.PLAYING)
            .all()
        )

        total_players = len(db.query(Player).filter(Player.game_id == game_id).all())

        result = {"phase": None, "eliminated_player": None}

        if game.phase == GamePhase.BUNKER_REVEAL:
            # Reveal bunker card and move to card reveal phase
            GameService.reveal_bunker_card(db, game_id)
            game.phase = GamePhase.CARD_REVEAL
            duration = get_phase_duration("card_reveal", len(players))
            game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)

        elif game.phase == GamePhase.CARD_REVEAL:
            # Move to discussion
            game.phase = GamePhase.DISCUSSION
            duration = get_phase_duration("discussion")
            game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)

        elif game.phase == GamePhase.DISCUSSION:
            # Move to voting (if this round has voting)
            votings = get_votings_for_round(total_players, game.current_round)
            if votings > 0:
                game.phase = GamePhase.VOTING
                duration = get_phase_duration("voting")
                game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)
            else:
                # Skip voting, go to next round
                GameService._next_round(db, game, players, total_players)

        elif game.phase == GamePhase.VOTING:
            game.phase = GamePhase.REVEAL
            duration = get_phase_duration("reveal")
            game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)

        elif game.phase == GamePhase.REVEAL:
            # Eliminate player and check if game should end
            eliminated = GameService.eliminate_player(db, game_id)

            if eliminated:
                result["eliminated_player"] = {
                    "id": eliminated.id,
                    "name": eliminated.name,
                    "revealed_cards": eliminated.revealed_cards,
                }

            # Reset votes for next round
            for player in players:
                player.votes_received = 0
                player.has_voted = False
                player.voted_for = None

            GameService._next_round(db, game, players, total_players)

        db.commit()
        db.refresh(game)
        result["phase"] = game.phase
        return result

    @staticmethod
    def _next_round(db: Session, game: Game, players: List[Player], total_players: int):
        """Move to next round or end game"""
        alive_count = len([p for p in players if p.status == PlayerStatus.PLAYING])
        bunker_capacity = get_bunker_capacity(total_players)
        max_rounds = get_max_rounds(total_players)

        # Reset votes for all players when moving to next round
        for player in players:
            player.votes_received = 0
            player.has_voted = False
            player.voted_for = None

        if alive_count <= bunker_capacity or game.current_round >= max_rounds:
            # Game over - move to survival check or end
            if game.mode == GameMode.SURVIVAL_STORY:
                game.phase = GamePhase.SURVIVAL_CHECK
                duration = get_phase_duration("survival_check")
                game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)
                GameService._assign_threat_cards(db, game.id, players)
            else:
                game.phase = GamePhase.ENDED
                game.ended_at = datetime.utcnow()
                game.phase_end_time = None  # No timer for ended phase
                for player in players:
                    if player.status == PlayerStatus.PLAYING:
                        player.status = PlayerStatus.SURVIVED
        else:
            # Next round
            game.current_round += 1
            game.phase = GamePhase.BUNKER_REVEAL
            duration = get_phase_duration("bunker_reveal")
            game.phase_end_time = datetime.utcnow() + timedelta(seconds=duration)

    @staticmethod
    def _assign_threat_cards(db: Session, game_id: int, players: List[Player]):
        """Assign threat cards for survival story mode"""
        alive_players = [p for p in players if p.status == PlayerStatus.PLAYING]
        threat_cards = get_random_threat_cards(len(alive_players))

        for i, player in enumerate(alive_players):
            if i < len(threat_cards):
                player.threat_card = threat_cards[i]

        db.commit()

    @staticmethod
    def vote_player(db: Session, game_id: int, voter_id: int, target_id: int) -> bool:
        """Register a vote"""
        game = db.query(Game).filter(Game.id == game_id).first()

        if not game or game.phase != GamePhase.VOTING:
            return False

        voter = db.query(Player).filter(Player.id == voter_id).first()
        target = db.query(Player).filter(Player.id == target_id).first()

        if not voter or not target or voter.has_voted:
            return False

        # Eliminated players can't vote
        if voter.status != PlayerStatus.PLAYING:
            return False

        # Can't vote for eliminated players
        if target.status != PlayerStatus.PLAYING:
            return False

        # Can't vote for yourself
        if voter_id == target_id:
            return False

        target.votes_received += 1
        voter.has_voted = True
        voter.voted_for = target_id

        db.commit()
        return True

    @staticmethod
    def eliminate_player(db: Session, game_id: int) -> Optional[Player]:
        """Eliminate player with most votes"""
        players = (
            db.query(Player)
            .filter(Player.game_id == game_id, Player.status == PlayerStatus.PLAYING)
            .all()
        )

        if not players:
            return None

        # Find player(s) with most votes
        max_votes = max(p.votes_received for p in players)

        # Don't eliminate anyone if no votes were cast
        if max_votes == 0:
            print(f"DEBUG: No votes cast, no elimination for game {game_id}")
            return None

        candidates = [p for p in players if p.votes_received == max_votes]
        print(
            f"DEBUG: Elimination candidates for game {game_id}: {[c.name for c in candidates]}, max_votes: {max_votes}"
        )

        # If tie, random choice
        eliminated = random.choice(candidates) if candidates else None

        if eliminated:
            print(f"DEBUG: Eliminating player {eliminated.name} with {max_votes} votes")
            eliminated.status = PlayerStatus.ELIMINATED
            # Reveal all cards except special condition
            all_cards = ["profession", "biology", "health", "hobby", "baggage", "fact"]
            eliminated.revealed_cards = all_cards
            flag_modified(eliminated, "revealed_cards")  # Important for JSON fields!

            db.commit()
            db.refresh(eliminated)

        return eliminated
