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
        timeRemaining: 0,
        timerInterval: null,
        leftSidebarOpen: false,
        rightSidebarOpen: false,

        async init() {
            await this.loadGameData();
            await this.loadMyCharacter();
            await this.loadMessages();
            this.connectWebSocket();
            this.startTimer();
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
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${this.gameCode}`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                // Reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
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
                    this.loadGameData();
                    break;
                case 'player_left':
                    this.loadGameData();
                    break;
                case 'phase_change':
                    this.game.phase = data.data.phase;
                    this.game.phase_end_time = data.data.phase_end_time;
                    this.loadGameData();
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
            }
        },

        handleGameUpdate(data) {
            this.game.phase = data.phase;
            this.game.current_round = data.current_round;
            this.game.phase_end_time = data.phase_end_time;

            if (data.players) {
                this.players = data.players;
                this.myPlayer = this.players.find(p => p.is_me) || null;
            }
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
            alert(`${data.player_name} використав особливу умову: ${data.special_name}`);
            this.loadGameData();
        },

        handleVoteUpdate(data) {
            // Update vote counts
            Object.keys(data).forEach(playerId => {
                const player = this.players.find(p => p.id === parseInt(playerId));
                if (player) {
                    player.votes_received = data[playerId];
                }
            });
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

        startTimer() {
            if (this.timerInterval) clearInterval(this.timerInterval);

            this.timerInterval = setInterval(() => {
                if (this.game.phase_end_time) {
                    // Fix for UTC time parsing: ensure 'Z' is present
                    const timeStr = this.game.phase_end_time.endsWith('Z')
                        ? this.game.phase_end_time
                        : this.game.phase_end_time + 'Z';

                    const endTime = new Date(timeStr);
                    const now = new Date();
                    const diff = Math.max(0, Math.floor((endTime - now) / 1000));
                    this.timeRemaining = diff;

                    // Debug logging for timer
                    if (this.game.phase === 'bunker_reveal') {
                        console.log(`[TIMER] Phase: ${this.game.phase}, Remaining: ${diff}s, isHost: ${this.isHost}, isAdvancing: ${this.isAdvancing}`);
                    }

                    // Auto-advance phase when timer expires
                    if (diff === 0 && this.isHost && !this.isAdvancing) {
                        console.log('[TIMER] Time expired! Auto-advancing phase...');
                        this.isAdvancing = true;
                        this.advancePhase();
                    }
                } else {
                    this.timeRemaining = 0;
                    if (this.game.phase === 'bunker_reveal') {
                        console.log('[TIMER] No phase_end_time set for bunker_reveal phase!');
                    }
                }
            }, 1000);
        },

        async advancePhase() {
            // Prevent rapid double-clicks
            if (this.isAdvancing) {
                console.log('Already advancing phase, please wait...');
                return;
            }

            const gameId = this.game.id;
            this.isAdvancing = true;

            try {
                const response = await fetch(`/api/games/${gameId}/advance-phase`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error('Failed to advance phase');
                }
                
                // Phase will update via WebSocket
                console.log('Phase advanced successfully');
            } catch (err) {
                console.error('Advance phase error:', err);
                alert('Помилка при переході до наступної фази');
            } finally {
                // Reset flag after delay to allow phase change to propagate
                setTimeout(() => {
                    this.isAdvancing = false;
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
            return this.players.length;
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
