// Card Templates and Colors
const CARD_COLORS = {
    profession: {
        border: '#3b82f6',  // Blue
        bg: 'rgba(59, 130, 246, 0.1)',
        glow: 'rgba(59, 130, 246, 0.3)',
        icon: '🎭'
    },
    biology: {
        border: '#10b981',  // Green
        bg: 'rgba(16, 185, 129, 0.1)',
        glow: 'rgba(16, 185, 129, 0.3)',
        icon: '🧬'
    },
    health: {
        border: '#ef4444',  // Red
        bg: 'rgba(239, 68, 68, 0.1)',
        glow: 'rgba(239, 68, 68, 0.3)',
        icon: '💊'
    },
    hobby: {
        border: '#eab308',  // Yellow
        bg: 'rgba(234, 179, 8, 0.1)',
        glow: 'rgba(234, 179, 8, 0.3)',
        icon: '🎨'
    },
    baggage: {
        border: '#92400e',  // Brown
        bg: 'rgba(146, 64, 14, 0.1)',
        glow: 'rgba(146, 64, 14, 0.3)',
        icon: '🎒'
    },
    fact: {
        border: '#a855f7',  // Purple
        bg: 'rgba(168, 85, 247, 0.1)',
        glow: 'rgba(168, 85, 247, 0.3)',
        icon: '📄'
    },
    special_condition: {
        border: '#f59e0b',  // Gold
        bg: 'rgba(245, 158, 11, 0.1)',
        glow: 'rgba(245, 158, 11, 0.3)',
        icon: '⭐'
    },
    catastrophe: {
        border: '#000000',  // Black
        bg: 'rgba(0, 0, 0, 0.5)',
        glow: 'rgba(239, 68, 68, 0.5)',
        icon: '☢️'
    },
    bunker: {
        border: '#6b7280',  // Gray
        bg: 'rgba(107, 116, 128, 0.1)',
        glow: 'rgba(107, 116, 128, 0.3)',
        icon: '🏠'
    },
    threat: {
        border: '#7f1d1d',  // Dark red
        bg: 'rgba(127, 29, 29, 0.2)',
        glow: 'rgba(127, 29, 29, 0.5)',
        icon: '⚠️'
    }
};

// Card labels in Ukrainian
const CARD_LABELS = {
    profession: 'Професія',
    biology: 'Біологія',
    health: 'Здоров\'я',
    hobby: 'Хобі',
    baggage: 'Багаж',
    fact: 'Факт',
    special_condition: 'Особлива Умова',
    catastrophe: 'Катастрофа',
    bunker: 'Бункер',
    threat: 'Загроза'
};

// Create card HTML element
function createCard(type, content, isRevealed = true, onClick = null) {
    const colors = CARD_COLORS[type] || CARD_COLORS.profession;
    const label = CARD_LABELS[type] || type;

    const card = document.createElement('div');
    card.className = `game-card-item ${isRevealed ? 'revealed' : 'hidden'} ${type}-card`;
    card.style.borderColor = colors.border;
    card.style.boxShadow = `0 0 15px ${colors.glow}`;

    if (onClick) {
        card.style.cursor = 'pointer';
        card.addEventListener('click', onClick);
    }

    if (!isRevealed) {
        // Card back design
        card.innerHTML = `
            <div class="card-back">
                <div class="card-pattern"></div>
                <div class="card-back-icon">🃏</div>
                <div class="card-back-text">БУНКЕР</div>
            </div>
        `;
    } else {
        // Card front design
        card.innerHTML = `
            <div class="card-front">
                <div class="card-header" style="background: ${colors.bg}; border-bottom: 2px solid ${colors.border};">
                    <span class="card-icon">${colors.icon}</span>
                    <span class="card-label">${label}</span>
                </div>
                <div class="card-content">
                    <div class="card-text">${content || '???'}</div>
                </div>
            </div>
        `;
    }

    return card;
}

// Create simplified card for display
function createSimpleCard(type, content) {
    const colors = CARD_COLORS[type] || CARD_COLORS.profession;
    const label = CARD_LABELS[type] || type;

    return `
        <div class="simple-card" style="border-color: ${colors.border}; background: ${colors.bg};">
            <div class="simple-card-header">
                <span>${colors.icon}</span>
                <span>${label}</span>
            </div>
            <div class="simple-card-content">${content || '???'}</div>
        </div>
    `;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CARD_COLORS, CARD_LABELS, createCard, createSimpleCard };
}
