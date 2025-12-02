# 🚀 Інструкція з деплою на сервер

## Варіант 1: Деплой через Docker (Рекомендований)

### Вимоги
- Docker встановлений на сервері
- Docker Compose встановлений

### Крок 1: Завантажити проект на сервер

```bash
# Через git
git clone <ваш-репозиторій>
cd bunker-game

# Або завантажити zip та розпакувати
scp -r bunker-game user@your-server:/path/to/
```

### Крок 2: Запустити деплой скрипт

```bash
chmod +x deploy-server.sh
./deploy-server.sh
```

Гра буде доступна за адресою: **http://YOUR_SERVER_IP:8765**

### Корисні команди Docker

```bash
# Переглянути логи
docker-compose logs -f

# Зупинити контейнери
docker-compose down

# Перезапустити
docker-compose restart

# Оновити після змін
docker-compose up -d --build
```

---

## Варіант 2: Ручний деплой (без Docker)

### Вимоги
- Python 3.11+
- pip

### Крок 1: Встановити залежності

```bash
cd bunker-game
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Крок 2: Запустити сервер

```bash
# Для доступу з будь-якої IP адреси на порту 8765
uvicorn backend.app.main:app --host 0.0.0.0 --port 8765

# Або з автоматичним перезапуском при змінах (dev mode)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8765 --reload
```

### Крок 3: Зробити сервіс systemd (опціонально, для автостарту)

Створіть файл `/etc/systemd/system/bunker-game.service`:

```ini
[Unit]
Description=Bunker Game Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/bunker-game
Environment="PATH=/path/to/bunker-game/venv/bin"
ExecStart=/path/to/bunker-game/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8765
Restart=always

[Install]
WantedBy=multi-user.target
```

Запустити сервіс:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bunker-game
sudo systemctl start bunker-game
sudo systemctl status bunker-game
```

---

## Варіант 3: Деплой через Nginx (для production)

### Крок 1: Встановити Nginx

```bash
sudo apt update
sudo apt install nginx
```

### Крок 2: Налаштувати Nginx як reverse proxy

Створіть файл `/etc/nginx/sites-available/bunker-game`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # або IP адреса

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_read_timeout 86400;
    }
}
```

Активувати конфігурацію:

```bash
sudo ln -s /etc/nginx/sites-available/bunker-game /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Тепер гра доступна на порту 80 (стандартний HTTP).

---

## 🔥 Налаштування Firewall

### UFW (Ubuntu/Debian)

```bash
# Дозволити порт 8765
sudo ufw allow 8765/tcp

# Або якщо використовуєте Nginx
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp  # для HTTPS

sudo ufw enable
```

### firewalld (CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-port=8765/tcp
sudo firewall-cmd --reload
```

---

## 🌐 Доступ до гри

Після запуску, гра буде доступна:

- **Локальна мережа**: `http://192.168.x.x:8765`
- **Публічний IP**: `http://YOUR_PUBLIC_IP:8765`
- **З доменом**: `http://your-domain.com` (якщо налаштували Nginx)

Гравці можуть підключитись з будь-якого пристрою в мережі, використовуючи цю адресу.

---

## 📊 Моніторинг

### Переглянути активні з'єднання

```bash
# Docker
docker-compose logs -f app

# Systemd
sudo journalctl -u bunker-game -f

# Прямий запуск
# Дивіться вивід у термінал
```

---

## 🔒 Безпека

### Для production рекомендується:

1. **Використовувати HTTPS** (Let's Encrypt)
2. **Змінити SECRET_KEY** в `backend/app/config.py`
3. **Налаштувати rate limiting**
4. **Використовувати PostgreSQL** замість SQLite
5. **Backup бази даних**

### Додати SSL через Certbot (безкоштовний HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🐛 Troubleshooting

### Порт вже зайнятий

```bash
# Перевірити що використовує порт 8765
sudo lsof -i :8765

# Або
sudo netstat -tulpn | grep 8765

# Вбити процес
sudo kill -9 <PID>
```

### База даних не створюється

```bash
# Перевірити права доступу
ls -la data/

# Створити директорію вручну
mkdir -p data
chmod 755 data
```

### WebSocket не працює

Переконайтесь що:
- Firewall дозволяє порт 8765
- Nginx правильно налаштований для WebSocket (якщо використовуєте)
- Клієнт використовує правильний протокол (ws:// або wss://)

---

## 📝 Примітки

- **Порт 8765** обраний для уникнення конфліктів з іншими сервісами
- **SQLite база** зберігається в `./data/bunker_game.db`
- **Логи Docker** можна переглянути через `docker-compose logs`
- **Автоматичний restart** налаштований через `restart: unless-stopped`
