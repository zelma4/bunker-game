// Landing Page Logic
function landingPage() {
    return {
        showCreateModal: false,
        showJoinModal: false,
        playerName: '',
        gameCode: '',
        gameMode: 'basic',  // 'basic' or 'survival_story'
        gameGoal: 'salvation',  // 'salvation' or 'rebirth'
        loading: false,
        error: '',

        async createGame() {
            this.loading = true;
            this.error = '';

            try {
                const response = await fetch('/api/games/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        player_name: this.playerName,
                        mode: this.gameMode,
                        goal: this.gameGoal
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to create game');
                }

                const data = await response.json();

                // Redirect to game page
                window.location.href = `/game/${data.code}`;
            } catch (err) {
                this.error = 'Помилка створення гри. Спробуйте ще раз.';
                console.error('Create game error:', err);
            } finally {
                this.loading = false;
            }
        },

        async joinGame() {
            this.loading = true;
            this.error = '';

            try {
                const response = await fetch('/api/games/join', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: this.gameCode.toUpperCase(),
                        player_name: this.playerName
                    })
                });

                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Гру не знайдено або вона вже почалася');
                    }
                    throw new Error('Failed to join game');
                }

                const data = await response.json();

                // Redirect to game page
                window.location.href = `/game/${data.code}`;
            } catch (err) {
                this.error = err.message || 'Помилка приєднання. Перевірте код та спробуйте ще раз.';
                console.error('Join game error:', err);
            } finally {
                this.loading = false;
            }
        }
    };
}
