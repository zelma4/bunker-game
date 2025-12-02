"""
Special Conditions Logic
Handles the execution of all 32 special condition effects
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, Dict, Any
import random

from ..models import Game, Player, PlayerStatus, GamePhase


class SpecialConditionHandler:
    """Handles execution of special condition effects"""

    @staticmethod
    def execute(
        db: Session,
        game_id: int,
        player_id: int,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a player's special condition
        
        Args:
            db: Database session
            game_id: Game ID
            player_id: Player ID who is using their special
            params: Additional parameters (e.g., target_player_id, card_type)
            
        Returns:
            Dict with result and message
        """
        if params is None:
            params = {}

        # Get player and game
        player = db.query(Player).filter(
            Player.id == player_id,
            Player.game_id == game_id
        ).first()

        if not player or not player.special_condition:
            return {"success": False, "message": "No special condition"}

        if player.special_used:
            return {"success": False, "message": "Already used"}

        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"success": False, "message": "Game not found"}

        special_name = player.special_condition.get("name")

        # Execute based on special name
        handler_map = {
            "Секс наостанок": SpecialConditionHandler._sex_last,
            "Віддай картку здоров'я": SpecialConditionHandler._swap_health,
            "Заручник": SpecialConditionHandler._hostage,
            "Антидот": SpecialConditionHandler._antidote,
            "Шпигун": SpecialConditionHandler._spy,
            "Диверсант": SpecialConditionHandler._saboteur,
            "Лідер": SpecialConditionHandler._leader,
            "Інженер": SpecialConditionHandler._engineer,
            "Детектив": SpecialConditionHandler._detective,
            "Психолог": SpecialConditionHandler._psychologist,
            "Миротворець": SpecialConditionHandler._peacemaker,
            "Судія": SpecialConditionHandler._judge,
            "Мафіозі": SpecialConditionHandler._mafia,
            "Сплячий агент": SpecialConditionHandler._sleeper_agent,
            "Телепат": SpecialConditionHandler._telepath,
            "Ворожка": SpecialConditionHandler._fortune_teller,
            "Хакер": SpecialConditionHandler._hacker,
            "Дипломат": SpecialConditionHandler._diplomat,
            "Революціонер": SpecialConditionHandler._revolutionary,
            "Страж": SpecialConditionHandler._guardian,
            "Клон": SpecialConditionHandler._clone,
            "Мутант": SpecialConditionHandler._mutant,
            "Санітар": SpecialConditionHandler._medic,
            "Берсерк": SpecialConditionHandler._berserker,
            "Привид": SpecialConditionHandler._ghost,
            "Оракул": SpecialConditionHandler._oracle,
            "Ілюзіоніст": SpecialConditionHandler._illusionist,
            "Магніт": SpecialConditionHandler._magnet,
            "Провокатор": SpecialConditionHandler._provocateur,
            "Анархіст": SpecialConditionHandler._anarchist,
            "Торговець": SpecialConditionHandler._trader,
            "Нейтральна зона": SpecialConditionHandler._neutral,
        }

        handler = handler_map.get(special_name)
        if not handler:
            return {"success": False, "message": f"Unknown special: {special_name}"}

        try:
            result = handler(db, game, player, params)
            
            if result.get("success"):
                # Mark as used only if successful
                player.special_used = True
                db.commit()
                
            return result
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error: {str(e)}"}

    # ==================== Special Condition Implementations ====================

    @staticmethod
    def _sex_last(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Секс наостанок: Пара різної статі отримує +1 голос кожен"""
        # This is passive - affects voting weight
        # Mark as "used" means it's activated for final check
        return {
            "success": True,
            "message": "Особлива умова активована. Буде враховано при перевірці виживання.",
            "effect": "passive"
        }

    @staticmethod
    def _swap_health(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Віддай картку здоров'я: Обміняти картку здоров'я"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        target = db.query(Player).filter(
            Player.id == target_id,
            Player.game_id == game.id
        ).first()

        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        # Swap health cards
        player.health, target.health = target.health, player.health
        db.commit()

        return {
            "success": True,
            "message": f"Картки здоров'я обмінано з {target.name}",
            "effect": "swap_health",
            "target_player_id": target_id
        }

    @staticmethod
    def _hostage(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Заручник: Якщо вигнано - забирає когось з собою"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        # Store target in player data (will be checked on elimination)
        if not hasattr(player, 'special_data'):
            player.special_data = {}
        
        player.special_data = {"hostage_target": target_id}
        flag_modified(player, "special_data")
        db.commit()

        return {
            "success": True,
            "message": "Заручник обрано. Якщо вас вигонять - він іде з вами.",
            "effect": "hostage_set",
            "target_player_id": target_id
        }

    @staticmethod
    def _antidote(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Антидот: Вилікувати хворобу"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        target = db.query(Player).filter(
            Player.id == target_id,
            Player.game_id == game.id
        ).first()

        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        # Set health to "Здоровий як бик"
        old_health = target.health
        target.health = "Здоровий як бик (вилікувано)"
        db.commit()

        return {
            "success": True,
            "message": f"Вилікувано {target.name}: {old_health} → Здоровий як бик",
            "effect": "heal",
            "target_player_id": target_id
        }

    @staticmethod
    def _spy(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Шпигун: Подивитись закриту картку"""
        target_id = params.get("target_player_id")
        card_type = params.get("card_type")
        
        if not target_id or not card_type:
            return {"success": False, "message": "Потрібен target_player_id та card_type"}

        target = db.query(Player).filter(
            Player.id == target_id,
            Player.game_id == game.id
        ).first()

        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        # Check if card is already revealed
        if card_type in (target.revealed_cards or []):
            return {"success": False, "message": "Картка вже відкрита"}

        # Get card value
        card_value = getattr(target, card_type, None)
        if not card_value:
            return {"success": False, "message": "Картка не знайдена"}

        return {
            "success": True,
            "message": f"Шпигун: {target.name} має {card_type}: {card_value}",
            "effect": "spy",
            "target_player_id": target_id,
            "card_type": card_type,
            "card_value": card_value
        }

    @staticmethod
    def _saboteur(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Диверсант: Скасувати один голос"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        if game.phase != GamePhase.VOTING:
            return {"success": False, "message": "Можна використати тільки під час голосування"}

        target = db.query(Player).filter(
            Player.id == target_id,
            Player.game_id == game.id
        ).first()

        if not target or target.votes_received <= 0:
            return {"success": False, "message": "У гравця немає голосів"}

        target.votes_received = max(0, target.votes_received - 1)
        db.commit()

        return {
            "success": True,
            "message": f"Скасовано 1 голос проти {target.name}",
            "effect": "cancel_vote",
            "target_player_id": target_id
        }

    @staticmethod
    def _leader(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Лідер: Подвійний голос"""
        # This is passive - affects vote weight
        return {
            "success": True,
            "message": "Активовано: Ваш голос тепер рахується подвійно",
            "effect": "double_vote"
        }

    @staticmethod
    def _engineer(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Інженер: +1 місце в бункері"""
        # This is passive - affects bunker capacity calculation
        return {
            "success": True,
            "message": "Додано +1 місце в бункері",
            "effect": "extra_bunker_slot"
        }

    @staticmethod
    def _detective(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Детектив: Поставити запитання - правда"""
        # This requires chat interaction - just mark as used
        return {
            "success": True,
            "message": "Поставте запитання в чаті. Гравець повинен відповісти правду.",
            "effect": "question_truth"
        }

    @staticmethod
    def _psychologist(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Психолог: Змінити голос гравця"""
        source_id = params.get("source_player_id")
        target_id = params.get("target_player_id")
        
        if not source_id or not target_id:
            return {"success": False, "message": "Потрібен source_player_id та target_player_id"}

        if game.phase != GamePhase.VOTING:
            return {"success": False, "message": "Тільки під час голосування"}

        source = db.query(Player).filter(Player.id == source_id).first()
        if not source or not source.has_voted:
            return {"success": False, "message": "Гравець ще не проголосував"}

        # Change vote
        old_target_id = source.voted_for
        if old_target_id:
            old_target = db.query(Player).filter(Player.id == old_target_id).first()
            if old_target:
                old_target.votes_received = max(0, old_target.votes_received - 1)

        new_target = db.query(Player).filter(Player.id == target_id).first()
        if new_target:
            new_target.votes_received += 1
            source.voted_for = target_id

        db.commit()

        return {
            "success": True,
            "message": f"Змінено голос гравця",
            "effect": "change_vote"
        }

    @staticmethod
    def _peacemaker(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Миротворець: Скасувати голосування"""
        if game.phase != GamePhase.VOTING:
            return {"success": False, "message": "Тільки під час голосування"}

        # Reset all votes
        players = db.query(Player).filter(Player.game_id == game.id).all()
        for p in players:
            p.votes_received = 0
            p.has_voted = False
            p.voted_for = None

        db.commit()

        return {
            "success": True,
            "message": "Голосування скасовано! Всі голоси обнулені.",
            "effect": "cancel_voting_round"
        }

    @staticmethod
    def _judge(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Судія: Вирішує нічию"""
        # This is passive - checked during tie-break
        return {
            "success": True,
            "message": "Активовано: При нічиї ви вирішуєте результат",
            "effect": "tiebreaker"
        }

    @staticmethod
    def _mafia(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Мафіозі: Погроза (блеф чи правда)"""
        # Chat-based, just mark as used
        return {
            "success": True,
            "message": "Можете погрожувати іншим гравцям. Блеф або правда - ваша справа.",
            "effect": "intimidate"
        }

    @staticmethod
    def _sleeper_agent(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Сплячий агент: Поміняти професію"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        target = db.query(Player).filter(
            Player.id == target_id,
            Player.game_id == game.id
        ).first()

        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        # Swap professions
        player.profession, target.profession = target.profession, player.profession
        db.commit()

        return {
            "success": True,
            "message": f"Професії обмінано з {target.name}",
            "effect": "swap_profession",
            "target_player_id": target_id
        }

    @staticmethod
    def _telepath(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Телепат: Вгадати закриту картку"""
        target_id = params.get("target_player_id")
        card_type = params.get("card_type")
        guess = params.get("guess")
        
        if not all([target_id, card_type, guess]):
            return {"success": False, "message": "Потрібен target_player_id, card_type, guess"}

        target = db.query(Player).filter(Player.id == target_id).first()
        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        actual_value = getattr(target, card_type, None)
        
        if guess.lower() == actual_value.lower():
            # Correct guess - reveal card
            if not target.revealed_cards:
                target.revealed_cards = []
            if card_type not in target.revealed_cards:
                target.revealed_cards.append(card_type)
                flag_modified(target, "revealed_cards")
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Правильно! {target.name} має {card_type}: {actual_value}",
                "effect": "reveal_card",
                "correct": True
            }
        else:
            return {
                "success": True,
                "message": f"Неправильно. Картка не відкрита.",
                "effect": "failed_guess",
                "correct": False
            }

    @staticmethod
    def _fortune_teller(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Ворожка: Передбачити результат голосування"""
        # Requires prediction before voting ends
        return {
            "success": True,
            "message": "Передбачте результат голосування в чаті. Якщо вірно - +2 голоси наступного раунду.",
            "effect": "predict_vote"
        }

    @staticmethod
    def _hacker(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Хакер: Подивитись 3 закритих картки Бункера"""
        if not game.bunker_cards or game.revealed_bunker_cards >= len(game.bunker_cards):
            return {"success": False, "message": "Всі картки бункера вже відкриті"}

        # Show next 3 unrevealed cards
        unrevealed = game.bunker_cards[game.revealed_bunker_cards:]
        preview = unrevealed[:3]

        return {
            "success": True,
            "message": f"Хакер: Наступні картки бункера: {', '.join(preview)}",
            "effect": "preview_bunker",
            "cards": preview
        }

    @staticmethod
    def _diplomat(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Дипломат: Альянс 3 гравців"""
        # Chat-based coalition
        return {
            "success": True,
            "message": "Організуйте альянс з 3 гравцями. Домовтесь голосувати разом.",
            "effect": "alliance"
        }

    @staticmethod
    def _revolutionary(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Революціонер: Перемішати всі закриті картки"""
        # This is VERY powerful - shuffle all unrevealed cards
        players = db.query(Player).filter(
            Player.game_id == game.id,
            Player.status == PlayerStatus.PLAYING
        ).all()

        card_types = ["profession", "biology", "health", "hobby", "baggage", "fact"]
        
        # Collect all unrevealed cards
        for card_type in card_types:
            unrevealed_players = [
                p for p in players 
                if card_type not in (p.revealed_cards or [])
            ]
            
            if len(unrevealed_players) <= 1:
                continue
                
            # Shuffle card values
            values = [getattr(p, card_type) for p in unrevealed_players]
            random.shuffle(values)
            
            for p, new_value in zip(unrevealed_players, values):
                setattr(p, card_type, new_value)

        db.commit()

        return {
            "success": True,
            "message": "Революція! Всі закриті картки перемішано!",
            "effect": "shuffle_cards"
        }

    @staticmethod
    def _guardian(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Страж: Захистити гравця від вигнання"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        # Store protected player
        if not hasattr(player, 'special_data'):
            player.special_data = {}
        
        player.special_data = {"protected_player": target_id, "round": game.current_round}
        flag_modified(player, "special_data")
        db.commit()

        return {
            "success": True,
            "message": "Гравець захищений цей раунд. Його не можна вигнати.",
            "effect": "protect",
            "target_player_id": target_id
        }

    @staticmethod
    def _clone(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Клон: Скопіювати відкриту картку"""
        target_id = params.get("target_player_id")
        card_type = params.get("card_type")
        
        if not target_id or not card_type:
            return {"success": False, "message": "Потрібен target_player_id та card_type"}

        target = db.query(Player).filter(Player.id == target_id).first()
        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        # Check if card is revealed
        if card_type not in (target.revealed_cards or []):
            return {"success": False, "message": "Картка не відкрита"}

        # Copy card value
        card_value = getattr(target, card_type)
        setattr(player, card_type, card_value)
        db.commit()

        return {
            "success": True,
            "message": f"Скопійовано {card_type}: {card_value}",
            "effect": "copy_card",
            "card_type": card_type
        }

    @staticmethod
    def _mutant(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Мутант: Поміняти 2 картки з кимось"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        target = db.query(Player).filter(Player.id == target_id).first()
        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        # Swap 2 random unrevealed cards
        card_types = ["profession", "biology", "health", "hobby", "baggage", "fact"]
        player_unrevealed = [c for c in card_types if c not in (player.revealed_cards or [])]
        target_unrevealed = [c for c in card_types if c not in (target.revealed_cards or [])]
        
        common = list(set(player_unrevealed) & set(target_unrevealed))
        if len(common) < 2:
            return {"success": False, "message": "Недостатньо закритих карток для обміну"}

        swap_cards = random.sample(common, 2)
        
        for card_type in swap_cards:
            player_val = getattr(player, card_type)
            target_val = getattr(target, card_type)
            setattr(player, card_type, target_val)
            setattr(target, card_type, player_val)

        db.commit()

        return {
            "success": True,
            "message": f"Обмінялись 2 картками з {target.name}",
            "effect": "swap_cards",
            "cards": swap_cards
        }

    @staticmethod
    def _medic(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Санітар: Вигнаний віддає картку"""
        # This is passive - triggers on elimination
        return {
            "success": True,
            "message": "При вигнанні гравця - отримаєте одну його картку",
            "effect": "loot_eliminated"
        }

    @staticmethod
    def _berserker(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Берсерк: Якщо вигнано - виганяє ще одного"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        # Store target (will be triggered on elimination)
        if not hasattr(player, 'special_data'):
            player.special_data = {}
        
        player.special_data = {"berserker_target": target_id}
        flag_modified(player, "special_data")
        db.commit()

        return {
            "success": True,
            "message": "Обрано ціль. Якщо вас вигонять - він іде з вами.",
            "effect": "berserker_set",
            "target_player_id": target_id
        }

    @staticmethod
    def _ghost(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Привид: Голосує ще 2 раунди після вигнання"""
        # This is passive - checked when player is eliminated
        return {
            "success": True,
            "message": "Після вигнання зможете голосувати ще 2 раунди",
            "effect": "ghost_vote"
        }

    @staticmethod
    def _oracle(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Оракул: Подивитись сторону B катастрофи"""
        if not game.catastrophe:
            return {"success": False, "message": "Немає катастрофи"}

        side_b = game.catastrophe.get("side_b", "Немає інформації")

        return {
            "success": True,
            "message": f"Сторона B: {side_b}",
            "effect": "view_catastrophe_b",
            "side_b": side_b
        }

    @staticmethod
    def _illusionist(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Ілюзіоніст: Приховати відкриту картку"""
        card_type = params.get("card_type")
        if not card_type:
            return {"success": False, "message": "Потрібен card_type"}

        if card_type not in (player.revealed_cards or []):
            return {"success": False, "message": "Картка не відкрита"}

        player.revealed_cards.remove(card_type)
        flag_modified(player, "revealed_cards")
        db.commit()

        return {
            "success": True,
            "message": f"Картку {card_type} приховано назад",
            "effect": "hide_card",
            "card_type": card_type
        }

    @staticmethod
    def _magnet(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Магніт: Картка бункера стає особистою"""
        if game.revealed_bunker_cards >= len(game.bunker_cards):
            return {"success": False, "message": "Всі картки вже відкриті"}

        # Take next bunker card
        next_card = game.bunker_cards[game.revealed_bunker_cards]
        
        if not hasattr(player, 'special_data'):
            player.special_data = {}
        
        player.special_data = {"personal_bunker_card": next_card}
        flag_modified(player, "special_data")
        db.commit()

        return {
            "success": True,
            "message": f"Картка бункера '{next_card}' тепер ваша особиста",
            "effect": "personal_bunker",
            "card": next_card
        }

    @staticmethod
    def _provocateur(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Провокатор: Двоє голосують один за одного"""
        player1_id = params.get("player1_id")
        player2_id = params.get("player2_id")
        
        if not player1_id or not player2_id:
            return {"success": False, "message": "Потрібен player1_id та player2_id"}

        # Store for voting phase
        if not hasattr(player, 'special_data'):
            player.special_data = {}
        
        player.special_data = {
            "forced_votes": {player1_id: player2_id, player2_id: player1_id}
        }
        flag_modified(player, "special_data")
        db.commit()

        return {
            "success": True,
            "message": "Двоє гравців тепер повинні голосувати один за одного",
            "effect": "force_votes"
        }

    @staticmethod
    def _anarchist(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Анархіст: Скасувати іншу Особливу Умову"""
        target_id = params.get("target_player_id")
        if not target_id:
            return {"success": False, "message": "Потрібен target_player_id"}

        target = db.query(Player).filter(Player.id == target_id).first()
        if not target:
            return {"success": False, "message": "Гравець не знайдений"}

        if not target.special_used:
            return {"success": False, "message": "Гравець ще не використав особливу умову"}

        # Cancel their special
        target.special_used = False
        db.commit()

        return {
            "success": True,
            "message": f"Скасовано особливу умову {target.name}",
            "effect": "cancel_special",
            "target_player_id": target_id
        }

    @staticmethod
    def _trader(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Торговець: Обміняти картку (за згодою)"""
        # This requires agreement - mark as initiated
        return {
            "success": True,
            "message": "Запропонуйте обмін іншому гравцю в чаті",
            "effect": "trade_offer"
        }

    @staticmethod
    def _neutral(db: Session, game: Game, player: Player, params: Dict) -> Dict:
        """Нейтральна зона: Немає особливої умови"""
        return {
            "success": False,
            "message": "У вас немає особливої умови"
        }
