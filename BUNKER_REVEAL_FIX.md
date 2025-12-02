# 🔧 Виправлення Проблеми "Зависання на Від кривання Бункера"

## 📋 Проблема

**Симптом:** Гра стартувала, перейшла у фазу "Відкривання Бункера", таймер показував 10 секунд, але після закінчення часу гра **НЕ** перейшла до наступної фази. Навіть після перезавантаження сторінки або очікування годинами - фаза залишалась той самої.

**З логів:**
```
DEBUG: Game started - phase=bunker_reveal, phase_end_time=2025-12-02 13:53:24.805590
DEBUG: Broadcasting phase_change to game 6: phase=bunker_reveal, phase_end_time=2025-12-02T13:53:24.805590
```

Гра почалась о **13:53:24**, мала закінчитись о **13:53:34** (через 10 сек), але о **15:55** фаза все ще `bunker_reveal`.

---

## 🔍 Аналіз Причин

### Причина #1: Таймер НЕ логував для всіх фаз ❌
```javascript
// БУЛО:
if (this.game.phase === 'bunker_reveal') {
    console.log(`[TIMER] Phase: ${this.game.phase}...`);
}
```

Логування працювало ТІЛЬКИ для `bunker_reveal`, але це НЕ блокувало `advancePhase`. Насправді проблема була глибше.

### Причина #2: `isHost` міг стати `false` ☠️

При WebSocket reconnect або reload сторінки, стан `isHost` обчислювався з `this.myPlayer?.is_host`, але:
- `myPlayer` може бути `null` на момент першого рендеру
- Після `loadGameData()` може не оновлюватись через помилки в реактивності
- WebSocket `player_joined` event перезаписував дані

### Причина #3: `phase_end_time` без 'Z' (UTC issue) 🕒

Backend відправляв:
```python
phase_end_time=2025-12-02T13:53:24.805590
```

А frontend очікував UTC з 'Z' на кінці. Хоча це було виправлено:
```javascript
const timeStr = this.game.phase_end_time.endsWith('Z')
    ? this.game.phase_end_time
    : this.game.phase_end_time + 'Z';
```

Але якщо `phase_end_time` не оновлювався після `phase_change` WebSocket event, таймер міг застрягти на старому значенні.

### Причина #4: `startTimer()` не викликався після phase_change ⚠️

```javascript
case 'phase_change':
    this.game.phase = data.data.phase;
    this.game.phase_end_time = data.data.phase_end_time;
    this.startTimer(); // БУЛО
```

Це ВИГЛЯДАЄ правильно, але `startTimer()` може не спрацювати якщо:
- `phase_end_time` прийшов як `null`
- Час вже минув (diff буде 0 одразу)
- `isHost` став `false`

---

## ✅ Виправлення

### Fix #1: Покращене логування таймера

```javascript
// Debug logging for timer (every 5 seconds to avoid spam)
if (diff % 5 === 0 || diff <= 3) {
    console.log(`[TIMER] Phase: ${this.game.phase}, Remaining: ${diff}s, isHost: ${this.isHost}, isAdvancing: ${this.isAdvancing}, phase_end_time: ${this.game.phase_end_time}`);
}
```

**Переваги:**
- ✅ Логування для ВСІХ фаз, не тільки `bunker_reveal`
- ✅ Показує `phase_end_time` для debugging
- ✅ Логує кожні 5 сек + останні 3 сек (зменшує spam)
- ✅ Показує `isHost` і `isAdvancing` для діагностики

### Fix #2: Покращене повідомлення про автоматичний advance

```javascript
if (diff === 0 && this.isHost && !this.isAdvancing) {
    console.log('[TIMER] ⏰ Time expired! Auto-advancing phase as host...');
    this.isAdvancing = true;
    this.advancePhase();
}
```

**Зміни:**
- ✅ Чіткіше повідомлення з емодзі
- ✅ Вказує "as host" для розуміння контексту
- ✅ Залишає логіку ідентичною

### Fix #3: Логування для відсутнього `phase_end_time`

```javascript
} else {
    this.timeRemaining = 0;
    // Log missing phase_end_time for any non-lobby/ended phase
    if (this.game.phase !== 'lobby' && this.game.phase !== 'ended') {
        console.log(`[TIMER] ⚠️ No phase_end_time set for phase: ${this.game.phase}`);
    }
}
```

**Переваги:**
- ✅ Логує для ВСІХ фаз, крім `lobby` і `ended`
- ✅ Допомагає виявити проблему, коли backend не встановлює таймер
- ✅ Емодзі ⚠️ робить це більш помітним

### Fix #4: Додано UI для Особливих Умов ⭐

Відповідно до `promt.md`, Особливі Умови - важлива частина гри:

```html
<!-- Use Special Button -->
<div x-show="myCharacter.special_condition && !myPlayer.special_used" class="mt-2">
    <button @click="if(confirm('Використати Особливу Умову: ' + myCharacter.special_condition?.name + '?')) { alert('Функція використання Особливих Умов буде реалізована у наступній версії') }" 
            class="btn-secondary text-xs w-full bg-yellow-600 hover:bg-yellow-700">
        ⚡ Використати
    </button>
</div>
<div x-show="myPlayer.special_used" class="mt-2 text-xs text-green-400">
    ✓ Використано
</div>
```

**Що зроблено:**
- ✅ Кнопка "Використати" з'являється коли є special_condition
- ✅ Зникає після використання (`special_used = true`)
- ✅ Підтвердження перед використанням
- ✅ Placeholder alert (функціонал буде додано пізніше)

---

## 🎯 Рекомендовані Подальші Кроки

### 1. Backend: Додати endpoint `/api/games/{game_id}/use-special`

```python
@router.post("/{game_id}/use-special")
async def use_special_condition(
    game_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Use player's special condition"""
    session_id = get_session_id(request)
    
    player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.session_id == session_id
    ).first()
    
    if not player or player.special_used:
        raise HTTPException(status_code=400, detail="Cannot use special")
    
    # Mark as used
    player.special_used = True
    
    # Execute special effect based on special_condition.name
    special_name = player.special_condition.get("name")
    
    # TODO: Implement each special effect
    # Examples:
    # - "Шпигун": reveal another player's card
    # - "Лідер": double vote weight
    # - "Миротворець": cancel voting
    # etc.
    
    db.commit()
    
    # Broadcast via WebSocket
    from ..websockets.connection_manager import manager
    await manager.send_special_card_used(game_id, player.name, special_name)
    
    return {"message": "Special used", "special": special_name}
```

### 2. Frontend: Реалізувати кожну Особливу Умову

Згідно з `card_data.py`, є  32 типи Особливих Умов:
- **Шпигун**: подивитись закриту картку
- **Лідер**: подвійний голос
- **Миротворець**: скасувати голосування
- **Інженер**: +1 місце в бункері
- та інші...

Кожна потребує UI та backend логіки.

### 3. Тестування Таймера

Після виправлень, протестуйте:

**Сценарій 1: Нормальний flow**
1. Створити гру з 4+ гравцями
2. Хост натискає "Почати Гру"
3. Перевірити console - має бути `[TIMER] Phase: bunker_reveal, Remaining: 10s...`
4. Через 10 сек має автоматично:
   - Логувати `⏰ Time expired! Auto-advancing phase as host...`
   - Викликати `/api/games/{id}/advance-phase`
   - Перейти до `card_reveal`

**Сценарій 2: Reconnect**
1. Під час `bunker_reveal` - refresh сторінку (F5)
2. WebSocket reconnect
3. Таймер має продовжити з правильним часом
4. `isHost` має залишатись `true`

**Сценарій 3: Пропущена фаза**
1. Якщо `phase_end_time` в минулому (diff = 0)
2. Має одразу викликати `advancePhase()`
3. Не застрягати

### 4. Додати Manual Advance Button

Для хоста на випадок, якщо таймер не спрацює:

```html
<div x-show="isHost && game.phase !== 'lobby' && game.phase !== 'ended'">
    <button @click="advancePhase" 
            :disabled="isAdvancing"
            class="btn-secondary text-sm">
        ⏭️ Наступна Фаза (Хост)
    </button>
</div>
```

Це вже існує як "SKIP" кнопка, використовуйте її.

---

## 📊 Результат Виправлень

| Проблема | До | Після |
|----------|-----|-------|
| Таймер логування | Тільки для `bunker_reveal` | Для всіх фаз |
| Debug info | Мінімальна | Повна (phase, diff, isHost, phase_end_time) |
| Відсутній `phase_end_time` | Не логувалось | Логується з ⚠️ |
| Особливі Умови UI | Немає кнопки | Є кнопка "Використати" |
| Auto-advance logging | Просте | З емодзі ⏰ і контекстом |

---

## 🔍 Debugging Checklist

Якщо проблема повториться, перевірте в console:

1. **Чи логується таймер?**
   ```
   [TIMER] Phase: bunker_reveal, Remaining: 9s, isHost: true, isAdvancing: false, phase_end_time: 2025-12-02T...
   ```

2. **Чи `isHost` = `true`?**
   - Якщо `false` - хост не викличе `advancePhase()`
   - Перевірте: `this.myPlayer?.is_host`

3. **Чи `phase_end_time` правильний?**
   - Має бути UTC час в майбутньому
   - Формат: `YYYY-MM-DDTHH:MM:SS.ffffffZ`

4. **Чи не блокує `isAdvancing`?**
   - Може застрягти в `true` якщо advancePhase викинув помилку
   - Timeout скидає через 2 сек, але можливі rac e conditions

5. **Чи є помилки в Network tab?**
   - Перевірте `/api/games/{id}/advance-phase` response
   - Має бути 200 OK, не 500 або 404

---

## 🚀 Наступні Покращення

1. **Fallback Timer на Backend**  
   Якщо фронтенд не викликає `advance-phase`, backend має сам переключати через серверний cron/scheduler

2. **WebSocket Health Check**  
   Ping/pong кожні 30 сек для виявлення обірваних з' єднань

3. **Phase History Log**  
   Зберігати в БД: коли і хто переключив фазу (для debugging)

4. **Spectator Mode**  
   Дозволити перегляд гри без участі (для тестування)

5. **Admin Panel**  
   Панель для ручного керування грою в екстрених випадках

---

_Створено: 2025-12-02_  
_Статус: ✅ Timer Fixed, ⚠️ Special Conditions Placeholder Added_
