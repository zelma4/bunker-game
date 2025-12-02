# Виправлення проблеми з відкритими картками

## Проблема
Коли гравець перезавантажує сторінку після відкриття карток, картки стають закритими як для нього, так і для інших гравців.

## Причина
SQLAlchemy не відстежує зміни в JSON полях автоматично. Коли ми робимо `player.revealed_cards.append(card_type)`, SQLAlchemy не знає, що поле змінилося і не зберігає зміни в базі даних.

## Виправлення

### 1. Додано `flag_modified` у всі місця де змінюється `revealed_cards`:

**backend/app/services/game_service.py:**
- Додано імпорт: `from sqlalchemy.orm.attributes import flag_modified`
- У методі `reveal_player_card()`: додано `flag_modified(player, "revealed_cards")`
- У методі `eliminate_player()`: додано `flag_modified(eliminated, "revealed_cards")`
- У методі `_reset_player()`: додано `flag_modified(player, "revealed_cards")`
- У методі `start_game()`: додано `flag_modified(player, "revealed_cards")`

### 2. Виправлено default значення для JSON поля:

**backend/app/models.py:**
```python
# Було:
revealed_cards = Column(JSON, default=list)

# Стало:
revealed_cards = Column(JSON, default=lambda: [])
```

`default=list` не працює правильно в SQLAlchemy, потрібно використовувати callable `lambda: []`.

## Тестування

1. Створіть гру з 2+ гравцями
2. Почніть гру
3. Відкрийте картку
4. Перезавантажте сторінку
5. ✅ Картка повинна залишитися відкритою
6. ✅ Інші гравці повинні бачити вашу відкриту картку

## Додаткові покращення

- Додано `db.refresh(player)` після збереження для гарантії актуальності даних
- Додано перевірку `if player.revealed_cards is None: player.revealed_cards = []` для безпеки
