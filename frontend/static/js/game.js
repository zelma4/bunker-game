// Game Page Logic
function gamePage(gameCode) {
    return {
        gameCode: gameCode,
        game: {
            id: null,
            phase: 'lobby',
            current_round: 0,
            phase_end_time: null,
            mode: 'basic',
            goal: 'salvation',
            catastrophe: null,
            bunker_cards: [],
            revealed_bunker_cards: 0
        },
        players: [],
        messages: [],
        gameLogs: [],  // Game event logs
        logIdCounter: 0,
        myPlayer: null,
        myCharacter: {
            profession: null,
            biology: null,
            health: null,
            hobby: null,
            baggage: null,
            fact: null,
            special_condition: null,
            revealed_cards: []
        },
        chatMessage: '',
        ws: null,
        wsConnecting: false,
        wsReconnectAttempts: 0,
        timeRemaining: 0,
        maxPhaseTime: 60,  // Default max time for timer circle
        timerInterval: null,
        leftSidebarOpen: false,
        rightSidebarOpen: false,
        isPaused: false,
        pausedTimeRemaining: 0,

        // Max rounds based on player count
        get maxRounds() {
            const count = this.players.length;
            if (count <= 4) return 3;
            if (count <= 6) return 4;
            return 5;
        },

        async init() {
            await this.loadGameData();
            await this.loadMyCharacter();
            await this.loadMessages();
            this.connectWebSocket();
            this.startTimer();

            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.close();
                }
            });
        },

        // Add game log entry
        addGameLog(message, type = 'info') {
            this.gameLogs.push({
                id: ++this.logIdCounter,
                message: message,
                type: type,
                timestamp: new Date().toISOString()
            });
            // Keep only last 100 logs
            if (this.gameLogs.length > 100) {
                this.gameLogs.shift();
            }
            // Scroll to bottom
            this.$nextTick(() => {
                const logsContainer = this.$refs.gameLogs;
                if (logsContainer) {
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                }
            });
        },

        formatLogTime(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            return date.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        },

        async loadGameData() {
            try {
                const response = await fetch(`/api/games/${this.gameCode}`);
                if (!response.ok) throw new Error('Game not found');

                const data = await response.json();
                this.game = {
                    id: data.id,
                    phase: data.phase,
                    current_round: data.current_round,
                    phase_end_time: data.phase_end_time,
                    mode: data.mode || 'basic',
                    goal: data.goal || 'salvation',
                    catastrophe: data.catastrophe,
                    bunker_cards: data.bunker_cards || [],
                    revealed_bunker_cards: data.revealed_bunker_cards || 0
                };
                this.players = data.players;

                // Find my player
                this.myPlayer = this.players.find(p => p.is_me) || null;
            } catch (err) {
                console.error('Load game error:', err);
                alert('Гру не знайдено!');
                window.location.href = '/';
            }
        },

        async loadMyCharacter() {
            if (this.game.phase === 'lobby') return;

            try {
                const response = await fetch(`/api/games/${this.game.id}/my-character`);
                if (response.ok) {
                    this.myCharacter = await response.json();
                }
            } catch (err) {
                console.error('Load character error:', err);
            }
        },

        async loadMessages() {
            try {
                const gameId = this.game.id;
                if (!gameId) return;

                const response = await fetch(`/api/chat/${gameId}/messages`);
                if (response.ok) {
                    this.messages = await response.json();
                    this.$nextTick(() => this.scrollChatToBottom());
                }
            } catch (err) {
                console.error('Load messages error:', err);
            }
        },

        connectWebSocket() {
            // Prevent duplicate connections
            if (this.wsConnecting) {
                console.log('[WS] Already connecting, skipping...');
                return;
            }

            // Close existing connection if any
            if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
                console.log('[WS] Closing existing connection');
                this.ws.close();
                this.ws = null;
            }

            this.wsConnecting = true;
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${this.gameCode}`;

            console.log('[WS] Connecting to:', wsUrl);
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('[WS] WebSocket connected');
                this.wsConnecting = false;
                this.wsReconnectAttempts = 0;

                // Request fresh game state when reconnecting
                if (this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'request_update' }));
                }
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onerror = (error) => {
                console.error('[WS] WebSocket error:', error);
                this.wsConnecting = false;
            };

            this.ws.onclose = () => {
                console.log('[WS] WebSocket disconnected');
                this.wsConnecting = false;

                // Exponential backoff for reconnection
                this.wsReconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.wsReconnectAttempts), 10000);

                console.log(`[WS] Reconnecting in ${delay}ms... (attempt ${this.wsReconnectAttempts})`);
                setTimeout(() => {
                    if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
                        this.connectWebSocket();
                    }
                }, delay);
            };
        },

        handleWebSocketMessage(data) {
            console.log('WebSocket message:', data);

            switch (data.type) {
                case 'game_update':
                    this.handleGameUpdate(data.data);
                    break;
                case 'chat':
                    this.handleChatMessage(data.data);
                    break;
                case 'player_joined':
                    console.log('[WS] Player joined:', data.data?.player_name);
                    this.addGameLog(`<strong>${data.data?.player_name}</strong> приєднався до гри`, 'join');
                    // Force reload game data to update player count
                    this.loadGameData().then(() => {
                        // Force Alpine reactivity
                        this.$nextTick(() => {
                            console.log('[WS] Player list updated, count:', this.playerCount);
                        });
                    });
                    break;
                case 'player_left':
                    console.log('[WS] Player left');
                    this.addGameLog('Гравець покинув гру', 'join');
                    this.loadGameData();
                    break;
                case 'phase_change':
                    console.log('[WS] Phase change received:', data.data);
                    const oldPhase = this.game.phase;
                    this.game.phase = data.data.phase;
                    this.game.phase_end_time = data.data.phase_end_time;
                    
                    // Update current_round if provided
                    if (data.data.current_round !== undefined && data.data.current_round !== null) {
                        this.game.current_round = data.data.current_round;
                    }
                    
                    // Log phase change
                    const phaseNames = {
                        'lobby': 'Лобі',
                        'bunker_reveal': '🏠 Відкриття бункера',
                        'card_reveal': '🎴 Відкриття карток',
                        'discussion': '💬 Обговорення',
                        'voting': '🗳️ Голосування',
                        'reveal': '📊 Результати',
                        'ended': '🏁 Гра завершена'
                    };
                    if (oldPhase !== this.game.phase) {
                        this.addGameLog(`Фаза: <strong>${phaseNames[this.game.phase] || this.game.phase}</strong>`, 'phase');
                    }
                    
                    console.log(`[WS] Phase changed from ${oldPhase} to ${this.game.phase}, round: ${this.game.current_round}, new end_time: ${this.game.phase_end_time}`);
                    
                    // Reset advancing flag and pause when phase changes
                    this.isAdvancing = false;
                    this.timerExpiredAt = null;
                    this.isPaused = false;
                    
                    // Update maxPhaseTime for timer circle
                    this.updateMaxPhaseTime();
                    
                    this.startTimer(); // Restart timer with new phase_end_time

                    // Reload character data if game started
                    if (this.game.phase !== 'lobby') {
                        this.loadMyCharacter();
                    }

                    // Force Alpine.js to update by using $nextTick
                    this.$nextTick(() => {
                        console.log('[WS] UI updated after phase change to:', this.game.phase);
                    });
                    break;
                case 'bunker_card_revealed':
                    this.handleBunkerCardRevealed(data.data);
                    break;
                case 'player_revealed_card':
                    this.handlePlayerCardRevealed(data.data);
                    break;
                case 'special_card_used':
                    this.handleSpecialCardUsed(data.data);
                    break;
                case 'vote_update':
                    this.handleVoteUpdate(data.data);
                    break;
                case 'player_eliminated':
                    this.handlePlayerEliminated(data.data);
                    break;
                case 'timer_paused':
                    this.isPaused = data.data.paused;
                    if (this.isPaused) {
                        this.pausedTimeRemaining = this.timeRemaining;
                        this.addGameLog('⏸️ Хост поставив гру на паузу', 'phase');
                    } else {
                        this.addGameLog('▶️ Гра продовжується', 'phase');
                    }
                    break;
            }
        },

        updateMaxPhaseTime() {
            const phaseTimes = {
                'bunker_reveal': 10,
                'card_reveal': 60 * this.players.filter(p => p.status === 'playing').length,
                'discussion': 60,
                'voting': 30,
                'reveal': 3
            };
            this.maxPhaseTime = phaseTimes[this.game.phase] || 60;
        },

        handleGameUpdate(data) {
            console.log('[WS] Game update received:', { phase: data.phase, phase_end_time: data.phase_end_time });
            this.game.phase = data.phase;
            this.game.current_round = data.current_round;
            this.game.phase_end_time = data.phase_end_time;

            if (data.players) {
                this.players = data.players;
                this.myPlayer = this.players.find(p => p.is_me) || null;
            }

            // Restart timer when game updates
            this.startTimer();
        },

        handleChatMessage(data) {
            // Check if message already exists
            if (!this.messages.find(m => m.message === data.message && m.player_name === data.player_name)) {
                this.messages.push({
                    player_name: data.player_name,
                    message: data.message,
                    timestamp: new Date().toISOString()
                });
                this.$nextTick(() => this.scrollChatToBottom());
            }
        },

        handleBunkerCardRevealed(data) {
            this.game.revealed_bunker_cards = data.revealed_count;
            this.addGameLog(`Відкрито картку бункера #${data.revealed_count}`, 'reveal');
            // Add animation to bunker card
            const cardEl = document.querySelector(`.bunker-card-${data.revealed_count - 1}`);
            if (cardEl) {
                cardEl.classList.add('flipping');
                setTimeout(() => cardEl.classList.remove('flipping'), 600);
            }
        },

        handlePlayerCardRevealed(data) {
            const player = this.players.find(p => p.id === data.player_id);
            if (player) {
                if (!player.revealed_cards) player.revealed_cards = [];
                if (!player.revealed_cards.includes(data.card_type)) {
                    player.revealed_cards.push(data.card_type);
                    
                    const cardNames = {
                        'profession': 'Професію',
                        'biology': 'Біологію',
                        'health': 'Здоров\'я',
                        'hobby': 'Хобі',
                        'baggage': 'Багаж',
                        'fact': 'Факт'
                    };
                    this.addGameLog(`<strong>${player.name}</strong> відкрив ${cardNames[data.card_type] || data.card_type}`, 'reveal');

                    // Update card value
                    if (data.card_value) {
                        player[data.card_type] = data.card_value;

                        // If this is my player, update myPlayer and myCharacter
                        if (player.is_me) {
                            this.myPlayer = player;
                            // Also update myCharacter so UI reflects the change
                            if (this.myCharacter) {
                                this.myCharacter[data.card_type] = data.card_value;
                            }
                        }
                    }

                    // Add flip animation
                    const cardEl = document.querySelector(`.player-${player.id}-card-${data.card_type}`);
                    if (cardEl) {
                        cardEl.classList.add('flipping');
                        setTimeout(() => cardEl.classList.remove('flipping'), 600);
                    }
                }
            }
        },

        handleSpecialCardUsed(data) {
            this.addGameLog(`<strong>${data.player_name}</strong> використав особливу умову: ${data.special_name}`, 'special');
            this.loadGameData();
        },

        handleVoteUpdate(data) {
            console.log('[WS] Vote update received:', data);
            // Update vote counts for all players
            Object.keys(data).forEach(playerId => {
                const player = this.players.find(p => p.id === parseInt(playerId));
                if (player) {
                    // Log if someone just voted (has_voted changed to true)
                    if (data[playerId].has_voted && !player.has_voted) {
                        this.addGameLog(`<strong>${player.name}</strong> проголосував`, 'vote');
                    }
                    
                    player.votes_received = data[playerId].votes_received;
                    player.has_voted = data[playerId].has_voted;
                    
                    // Also update myPlayer if this is the current player
                    if (this.myPlayer && player.id === this.myPlayer.id) {
                        this.myPlayer.votes_received = data[playerId].votes_received;
                        this.myPlayer.has_voted = data[playerId].has_voted;
                    }
                }
            });

            // Force Alpine.js reactivity
            this.$nextTick(() => {
                console.log('[WS] Votes updated in UI');
            });
        },

        handlePlayerEliminated(data) {
            console.log('[WS] Player eliminated:', data);
            const player = this.players.find(p => p.id === data.player_id);
            if (player) {
                player.status = 'eliminated';
                player.revealed_cards = data.revealed_cards || ['profession', 'biology', 'health', 'hobby', 'baggage', 'fact'];
                
                this.addGameLog(`☠️ <strong>${player.name}</strong> був вигнаний з бункера!`, 'eliminate');
            }
            
            // Refresh game data to get latest state
            this.loadGameData();
        },

        async sendMessage() {
            if (!this.chatMessage.trim()) return;

            const gameId = this.game.id;

            try {
                const response = await fetch(`/api/chat/${gameId}/messages`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: this.chatMessage
                    })
                });

                if (response.ok) {
                    const newMessage = await response.json();
                    this.messages.push(newMessage);
                    this.chatMessage = '';
                    this.$nextTick(() => this.scrollChatToBottom());

                    // Broadcast via WebSocket
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({
                            type: 'chat',
                            player_name: this.myPlayer?.name || 'Unknown',
                            message: newMessage.message
                        }));
                    }
                } else if (response.status === 429) {
                    alert('Занадто багато повідомлень! Зачекайте трохи.');
                }
            } catch (err) {
                console.error('Send message error:', err);
            }
        },

        async revealCard(cardType) {
            const gameId = this.game.id;

            try {
                const response = await fetch(`/api/games/${gameId}/reveal-card`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        card_type: cardType
                    })
                });

                if (response.ok) {
                    // Update local state
                    if (!this.myCharacter.revealed_cards) {
                        this.myCharacter.revealed_cards = [];
                    }
                    this.myCharacter.revealed_cards.push(cardType);

                    // Broadcast to others
                    this.loadGameData();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Не вдалося відкрити картку');
                }
            } catch (err) {
                console.error('Reveal card error:', err);
            }
        },

        async startGame() {
            const gameId = this.game.id;

            try {
                const response = await fetch(`/api/games/${gameId}/start`, {
                    method: 'POST'
                });

                if (response.ok) {
                    // Game started, wait for WebSocket update
                    console.log('Game started!');
                    await this.loadMyCharacter();
                    await this.loadGameData();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Не вдалося почати гру');
                }
            } catch (err) {
                console.error('Start game error:', err);
                alert('Помилка запуску гри');
            }
        },

        // Helper function to show player selection dialog
        showPlayerSelect(title, excludeSelf = true) {
            return new Promise((resolve) => {
                const availablePlayers = this.players.filter(p => 
                    p.status === 'playing' && (!excludeSelf || p.id !== this.myPlayer?.id)
                );
                
                if (availablePlayers.length === 0) {
                    alert('Немає доступних гравців для вибору');
                    resolve(null);
                    return;
                }
                
                const options = availablePlayers.map(p => `${p.id}: ${p.name}`).join('\n');
                const result = prompt(`${title}\n\nДоступні гравці:\n${options}\n\nВведіть номер гравця:`);
                
                if (result === null) {
                    resolve(null);
                    return;
                }
                
                const playerId = parseInt(result);
                const player = availablePlayers.find(p => p.id === playerId);
                
                if (!player) {
                    alert('Невірний номер гравця');
                    resolve(null);
                    return;
                }
                
                resolve(playerId);
            });
        },

        // Helper function to show card type selection
        showCardTypeSelect(title) {
            return new Promise((resolve) => {
                const cardTypes = [
                    { value: 'profession', label: '🎭 Професія' },
                    { value: 'biology', label: '🧬 Біологія' },
                    { value: 'health', label: '💊 Здоров\'я' },
                    { value: 'hobby', label: '🎨 Хобі' },
                    { value: 'baggage', label: '🎒 Багаж' },
                    { value: 'fact', label: '📄 Факт' }
                ];
                
                const options = cardTypes.map((c, i) => `${i + 1}: ${c.label}`).join('\n');
                const result = prompt(`${title}\n\n${options}\n\nВведіть номер (1-6):`);
                
                if (result === null) {
                    resolve(null);
                    return;
                }
                
                const index = parseInt(result) - 1;
                if (index < 0 || index >= cardTypes.length) {
                    alert('Невірний вибір');
                    resolve(null);
                    return;
                }
                
                resolve(cardTypes[index].value);
            });
        },

        async useSpecial() {
            const gameId = this.game.id;
            const special = this.myCharacter.special_condition;

            if (!special) {
                alert('У вас немає особливої умови');
                return;
            }

            // Collect parameters based on special type
            const specialName = special.name;
            const params = {};

            // Special conditions that need target player
            const needsTarget = [
                'Віддай картку здоров\'я', 'Заручник', 'Антидот', 'Диверсант',
                'Сплячий агент', 'Клон', 'Мутант', 'Берсерк', 'Анархіст'
            ];

            // Special conditions that need card type
            const needsCard = ['Шпигун', 'Ілюзіоніст'];

            // Special conditions that need multiple parameters
            const complex = ['Телепат', 'Психолог', 'Провокатор'];

            try {
                if (needsTarget.includes(specialName)) {
                    const targetId = await this.showPlayerSelect(`${specialName}\nОберіть гравця:`);
                    if (!targetId) return;
                    params.target_player_id = targetId;
                }

                if (specialName === 'Шпигун') {
                    const targetId = await this.showPlayerSelect('Шпигун\nОберіть гравця для шпигування:');
                    if (!targetId) return;
                    const cardType = await this.showCardTypeSelect('Яку картку хочете побачити?');
                    if (!cardType) return;
                    params.target_player_id = targetId;
                    params.card_type = cardType;
                }

                if (specialName === 'Телепат') {
                    const targetId = await this.showPlayerSelect('Телепат\nОберіть гравця:');
                    if (!targetId) return;
                    const cardType = await this.showCardTypeSelect('Яку картку вгадуєте?');
                    if (!cardType) return;
                    const guess = prompt('Введіть ваше припущення (що написано на картці):');
                    if (!guess) return;
                    params.target_player_id = targetId;
                    params.card_type = cardType;
                    params.guess = guess;
                }

                if (specialName === 'Психолог') {
                    const sourceId = await this.showPlayerSelect('Психолог\nОберіть гравця, чий голос змінити:');
                    if (!sourceId) return;
                    const targetId = await this.showPlayerSelect('Оберіть нову ціль голосування:');
                    if (!targetId) return;
                    params.source_player_id = sourceId;
                    params.target_player_id = targetId;
                }

                if (specialName === 'Провокатор') {
                    const player1 = await this.showPlayerSelect('Провокатор\nОберіть першого гравця:');
                    if (!player1) return;
                    const player2 = await this.showPlayerSelect('Оберіть другого гравця:', true);
                    if (!player2) return;
                    params.player1_id = player1;
                    params.player2_id = player2;
                }

                if (specialName === 'Ілюзіоніст') {
                    const cardType = await this.showCardTypeSelect('Ілюзіоніст\nЯку картку приховати?');
                    if (!cardType) return;
                    params.card_type = cardType;
                }

                // Confirm
                const confirmed = confirm(`Використати Особливу Умову: ${specialName}?`);
                if (!confirmed) return;

                // Make API call
                const response = await fetch(`/api/games/${gameId}/use-special`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(params)
                });

                if (response.ok) {
                    const result = await response.json();
                    alert(`✅ ${result.message}`);

                    // Refresh data
                    await this.loadGameData();
                    await this.loadMyCharacter();
                } else {
                    const error = await response.json();
                    alert(`❌ ${error.detail || 'Помилка використання особливої умови'}`);
                }
            } catch (err) {
                console.error('Use special error:', err);
                alert('Помилка при використанні особливої умови');
            }
        },

        async vote(targetPlayerId) {
            const gameId = this.game.id;

            try {
                const response = await fetch(`/api/games/${gameId}/vote`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        target_player_id: targetPlayerId
                    })
                });

                if (response.ok) {
                    this.myPlayer.has_voted = true;
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Помилка голосування');
                }
            } catch (err) {
                console.error('Vote error:', err);
            }
        },

        isAdvancing: false,
        timerExpiredAt: null, // Track when timer first hit 0

        startTimer() {
            if (this.timerInterval) clearInterval(this.timerInterval);
            this.timerExpiredAt = null; // Reset on new timer start

            // Debug: log time comparison on timer start
            if (this.game.phase_end_time) {
                const timeStr = this.game.phase_end_time.endsWith('Z')
                    ? this.game.phase_end_time
                    : this.game.phase_end_time + 'Z';
                const endTime = new Date(timeStr);
                const now = new Date();
                const diff = Math.floor((endTime - now) / 1000);
                console.log(`[TIMER START] phase_end_time=${this.game.phase_end_time}, endTime=${endTime.toISOString()}, now=${now.toISOString()}, diff=${diff}s`);
            }

            // Small delay before starting timer to ensure phase_change is fully processed
            setTimeout(() => {
                this.timerInterval = setInterval(() => {
                    // Skip timer updates if paused
                    if (this.isPaused) {
                        return;
                    }
                    
                    if (this.game.phase_end_time) {
                        // Fix for UTC time parsing: ensure 'Z' is present
                        const timeStr = this.game.phase_end_time.endsWith('Z')
                            ? this.game.phase_end_time
                            : this.game.phase_end_time + 'Z';

                        const endTime = new Date(timeStr);
                        const now = new Date();
                        const diff = Math.max(0, Math.floor((endTime - now) / 1000));
                        this.timeRemaining = diff;

                        // Debug logging for timer (every 5 seconds to avoid spam)
                        if (diff % 5 === 0 || diff <= 3) {
                            console.log(`[TIMER] Phase: ${this.game.phase}, Remaining: ${diff}s, isHost: ${this.isHost}, isAdvancing: ${this.isAdvancing}, phase_end_time: ${this.game.phase_end_time}`);
                        }

                        // Auto-advance phase when timer expires - ONLY HOST can auto-advance
                        if (diff === 0 && !this.isAdvancing && this.isHost) {
                            // Track when timer first expired
                            if (!this.timerExpiredAt) {
                                this.timerExpiredAt = Date.now();
                                console.log('[TIMER] ⏰ Timer expired! isHost:', this.isHost, 'Advancing phase...');
                                this.advancePhase();
                            }
                        } else if (diff === 0 && !this.isHost) {
                            // Non-host players just wait for phase_change from WebSocket
                            if (!this.timerExpiredAt) {
                                this.timerExpiredAt = Date.now();
                                console.log('[TIMER] ⏰ Timer expired, waiting for host to advance phase...');
                            }
                        }
                    } else {
                        this.timeRemaining = 0;
                        this.timerExpiredAt = null;
                        // Log missing phase_end_time for any non-lobby/ended phase
                        if (this.game.phase !== 'lobby' && this.game.phase !== 'ended') {
                            console.log(`[TIMER] ⚠️ No phase_end_time set for phase: ${this.game.phase}`);
                        }
                    }
                }, 1000);
            }, 100); // 100ms delay to ensure phase change is fully processed
        },

        async advancePhase() {
            console.log('[ADVANCE] advancePhase called, isAdvancing:', this.isAdvancing, 'gameId:', this.game.id);
            
            // Prevent rapid double-clicks
            if (this.isAdvancing) {
                console.log('[ADVANCE] Already advancing phase, please wait...');
                return;
            }

            const gameId = this.game.id;
            if (!gameId) {
                console.error('[ADVANCE] No game ID!');
                return;
            }
            
            this.isAdvancing = true;
            console.log('[ADVANCE] Calling /api/games/' + gameId + '/advance-phase');

            try {
                const response = await fetch(`/api/games/${gameId}/advance-phase`, {
                    method: 'POST'
                });

                console.log('[ADVANCE] Response status:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('[ADVANCE] Error response:', errorText);
                    throw new Error('Failed to advance phase');
                }

                const result = await response.json();
                console.log('[ADVANCE] Phase advanced successfully, result:', result);
            } catch (err) {
                console.error('[ADVANCE] Advance phase error:', err);
                // Don't show alert for every error, just log it
            } finally {
                // Reset flag after delay to allow phase change to propagate
                setTimeout(() => {
                    this.isAdvancing = false;
                    console.log('[ADVANCE] isAdvancing reset to false');
                }, 2000);
            }
        },

        async skipPhase() {
            if (!this.isHost) {
                alert('Тільки хост може пропускати фази!');
                return;
            }

            if (this.isAdvancing) {
                console.log('Already processing phase change...');
                return;
            }

            if (confirm('Пропустити поточну фазу та перейти до наступної?')) {
                await this.advancePhase();
            }
        },

        async togglePause() {
            if (!this.isHost) {
                alert('Тільки хост може ставити гру на паузу!');
                return;
            }

            this.isPaused = !this.isPaused;
            
            if (this.isPaused) {
                this.pausedTimeRemaining = this.timeRemaining;
                this.addGameLog('⏸️ Гра на паузі', 'phase');
            } else {
                this.addGameLog('▶️ Гра продовжується', 'phase');
                // Extend phase_end_time by the paused duration
                // This is a client-side pause, so we just stop the timer from advancing
            }
            
            // Broadcast pause state to other players via WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'pause_toggle',
                    paused: this.isPaused
                }));
            }
        },

        copyCode() {
            navigator.clipboard.writeText(this.gameCode);
            alert('Код скопійовано!');
        },

        scrollChatToBottom() {
            const chatEl = this.$refs.chatMessages;
            if (chatEl) {
                chatEl.scrollTop = chatEl.scrollHeight;
            }
        },

        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        },

        formatTimestamp(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
        },

        isCardRevealed(cardType) {
            return this.myCharacter.revealed_cards?.includes(cardType) || false;
        },

        canRevealCard(cardType) {
            if (this.game.phase !== 'card_reveal') return false;
            if (this.isCardRevealed(cardType)) return false;

            // First round must reveal profession
            if (this.game.current_round === 1 && cardType !== 'profession') {
                return false;
            }

            return true;
        },

        get phaseText() {
            const phases = {
                lobby: 'Очікування',
                bunker_reveal: 'Відкривання Бункера',
                card_reveal: 'Відкривання Карток',
                discussion: 'Обговорення',
                voting: 'Голосування',
                reveal: 'Результати',
                survival_check: 'Перевірка Виживання',
                ended: 'Завершено'
            };
            return phases[this.game.phase] || this.game.phase;
        },

        get playerCount() {
            // Force Alpine reactivity
            return Array.isArray(this.players) ? this.players.length : 0;
        },

        get isHost() {
            return this.myPlayer?.is_host || false;
        },

        get modeText() {
            return this.game.mode === 'basic' ? 'Базовий' : 'Історія Виживання';
        },

        get goalText() {
            return this.game.goal === 'salvation' ? 'Порятунок' : 'Відродження';
        }
    };
}
