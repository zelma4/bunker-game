# 🌐 Налаштування домену bunker.zelma4.me# 🌐 Налаштування домену bunker.zelma4.me


















































































































































































































































































































































































Готово! Тепер твоя гра буде доступна на **https://bunker.zelma4.me** 🎉---```echo "=== SSL ===" && sudo certbot certificatesecho "=== Nginx ===" && sudo nginx -t && \echo "=== Port 8765 ===" && sudo lsof -i :8765 && \echo "=== DNS ===" && nslookup bunker.zelma4.me && \```bash### Перевірка всього```sudo certbot --nginx -d bunker.zelma4.mesudo apt install nginx certbot python3-certbot-nginx -y && \sudo apt update && \```bash### Одна команда для SSL```TTL: AutomaticValue: <IP_ТВОГО_СЕРВЕРА>Host: bunkerType: A Record```### Налаштування DNS в Namecheap## 📝 Швидкі команди для копіювання---```sudo certbot --nginx -d bunker.zelma4.mesudo certbot delete --cert-name bunker.zelma4.me# Видалити і отримати зновуsudo certbot renew --force-renewal# Примусове оновленняsudo certbot certificates# Перевірити статус```bash### Certbot помилки```docker-compose restart# Перезапуститиdocker-compose logs -fdocker-compose ps# Перевірити Dockersudo netstat -tulpn | grep 8765sudo lsof -i :8765# Перевірити чи працює додаток```bash### Порт 8765 не відповідає```sudo systemctl restart nginx# Перезапустити Nginxsudo nginx -t# Перевірити конфігураціюsudo tail -f /var/log/nginx/bunker_access.logsudo tail -f /var/log/nginx/bunker_error.log# Перевірити логи```bash### Nginx помилки```ipconfig /flushdns# Windowssudo systemd-resolve --flush-caches# Linuxsudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder# macOS# Очистити локальний DNS кешdig NS zelma4.me# Перевірити NS сервери Namecheap```bash### DNS не працює## 🐛 Troubleshooting---- ♻️ **Автоматичне оновлення**: SSL сертифікат оновлюється автоматично- 🚀 **WebSocket**: Повна підтримка для real-time гри- 🔒 **SSL**: Безкоштовний сертифікат Let's Encrypt- 🌐 **Домен**: https://bunker.zelma4.meПісля всіх кроків гра буде доступна:## 🎯 Підсумок---```}    }        proxy_send_timeout 86400;        proxy_read_timeout 86400;        # Таймаути                proxy_set_header X-Forwarded-Proto $scheme;        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;        proxy_set_header X-Real-IP $remote_addr;        proxy_set_header Host $host;        # Headers                proxy_set_header Connection "upgrade";        proxy_set_header Upgrade $http_upgrade;        # WebSocket підтримка                proxy_http_version 1.1;        proxy_pass http://127.0.0.1:8765;    location / {    # Proxy до FastAPI    error_log /var/log/nginx/bunker_error.log;    access_log /var/log/nginx/bunker_access.log;    # Логи    client_max_body_size 10M;    # Розмір файлів    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;    include /etc/letsencrypt/options-ssl-nginx.conf;    ssl_certificate_key /etc/letsencrypt/live/bunker.zelma4.me/privkey.pem;    ssl_certificate /etc/letsencrypt/live/bunker.zelma4.me/fullchain.pem;    # SSL сертифікати (налаштовані certbot)    server_name bunker.zelma4.me;    listen [::]:443 ssl http2;    listen 443 ssl http2;server {# HTTPS Server}    return 301 https://$server_name$request_uri;    server_name bunker.zelma4.me;    listen [::]:80;    listen 80;server {# HTTP → HTTPS redirect```nginxПісля запуску `certbot`, твій `/etc/nginx/sites-available/bunker.zelma4.me` буде виглядати так:## Оновлена конфігурація після SSL---- **HTTPS** (після налаштування SSL): https://bunker.zelma4.me- **HTTP**: http://bunker.zelma4.me### 6.3 Відкрити в браузері```curl http://bunker.zelma4.me```bash### 6.2 Перевірити HTTP```Address: 123.45.67.89Name:	bunker.zelma4.meNon-authoritative answer:Address:	8.8.8.8#53Server:		8.8.8.8# Має повернути IP твого сервераnslookup bunker.zelma4.me# Локально або на сервері```bash### 6.1 Перевірити DNS## Крок 6: Перевірка роботи---```8765/tcp                   ALLOW       AnywhereNginx Full                 ALLOW       Anywhere--                         ------      ----To                         Action      FromStatus: active```Результат:```sudo ufw statussudo ufw enablesudo ufw allow 8765/tcp  # На всяк випадок для прямого доступуsudo ufw allow 'Nginx Full'# Дозволити HTTP, HTTPS та порт додатку```bash## Крок 5: Налаштування Firewall---```# Certbot автоматично оновлює сертифікати через cronsudo certbot renew --dry-run# Тестовий запуск оновлення```bash### 4.3 Перевірити автоматичне оновлення- Додасть автоматичне оновлення сертифіката- Налаштує автоматичне перенаправлення HTTP → HTTPS- Оновить конфігурацію Nginx- Отримає SSL сертифікатCertbot автоматично:```sudo certbot --nginx -d bunker.zelma4.me```bash### 4.2 Отримати SSL сертифікат```sudo apt install certbot python3-certbot-nginx -y# Ubuntu/Debian```bash### 4.1 Встановити Certbot## Крок 4: Додати HTTPS (SSL) через Let's Encrypt---```./run-local-8765.shcd /path/to/bunker-game```bash### 3.2 Або без DockerДодаток буде слухати на `127.0.0.1:8765`, а Nginx буде проксувати запити з `bunker.zelma4.me`.```./deploy-server.shcd /path/to/bunker-game```bash### 3.1 Через Docker (рекомендовано)## Крок 3: Запустити додаток---```sudo systemctl restart nginx# Перезапустити Nginxsudo nginx -t# Перевірити конфігураціюsudo ln -s /etc/nginx/sites-available/bunker.zelma4.me /etc/nginx/sites-enabled/# Створити symlink```bash### 2.3 Активувати конфігурацію```}    }        proxy_send_timeout 86400;        proxy_read_timeout 86400;        # Таймаути для WebSocket                proxy_set_header X-Forwarded-Proto $scheme;        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;        proxy_set_header X-Real-IP $remote_addr;        proxy_set_header Host $host;        # Headers                proxy_set_header Connection "upgrade";        proxy_set_header Upgrade $http_upgrade;        # WebSocket підтримка                proxy_http_version 1.1;        proxy_pass http://127.0.0.1:8765;    location / {    # Proxy до FastAPI на порту 8765    error_log /var/log/nginx/bunker_error.log;    access_log /var/log/nginx/bunker_access.log;    # Логи    client_max_body_size 10M;    # Розмір файлів    server_name bunker.zelma4.me;    listen [::]:80;    listen 80;server {# HTTP Server (буде перенаправляти на HTTPS після налаштування SSL)```nginxВставити наступну конфігурацію:```sudo nano /etc/nginx/sites-available/bunker.zelma4.me```bashСтвори файл `/etc/nginx/sites-available/bunker.zelma4.me`:### 2.2 Створити конфігурацію для bunker.zelma4.me```sudo systemctl status nginx# Перевірити статусsudo apt install nginx -ysudo apt update# Ubuntu/Debian```bash### 2.1 Встановити Nginx (якщо ще не встановлений)## Крок 2: Налаштування сервера з Nginx---- Перевір готовність: `nslookup bunker.zelma4.me`- Зазвичай працює протягом **15-30 хвилин**- DNS зміни можуть зайняти від **5 хвилин до 48 годин**### 1.3 Очікування поширення DNS```A Record    bunker    123.45.67.89      AutomaticType        Host      Value              TTL```**Приклад:**4. Натисни **Save All Changes** ✓   - **TTL**: `Automatic` або `300` (5 хвилин для швидкого оновлення)   - **Value**: `IP_АДРЕСА_ТВОГО_СЕРВЕРА` (наприклад, 123.45.67.89)   - **Host**: `bunker`   - **Type**: `A Record`3. Додай новий запис:2. В секції **Host Records** натисни **Add New Record**1. Перейди на вкладку **Advanced DNS**### 1.2 Додати A Record для субдомену4. Натисни **Manage** біля домену `zelma4.me`3. Перейди до **Domain List**2. Увійди в акаунт1. Зайди на https://www.namecheap.com### 1.1 Увійти в Namecheap## Крок 1: Налаштування DNS в Namecheap
## Крок 1: Налаштування DNS на Namecheap

### 1.1 Увійти в Namecheap
1. Зайти на https://www.namecheap.com
2. Увійти в акаунт
3. Перейти в Dashboard → Domain List
4. Знайти `zelma4.me` та натиснути **Manage**

### 1.2 Додати A-запис для субдомену

У розділі **Advanced DNS**:

1. Натисни **Add New Record**
2. Заповни поля:
   ```
   Type: A Record
   Host: bunker
   Value: YOUR_SERVER_IP  (наприклад, 123.45.67.89)
   TTL: Automatic (або 5 min)
   ```
3. Натисни зелену галочку ✓ для збереження

**Приклад:**
```
Type    Host     Value           TTL
A       bunker   123.45.67.89    Automatic
```

### 1.3 Перевірка (опціонально)
Через 5-10 хвилин перевір:
```bash
dig bunker.zelma4.me
# або
nslookup bunker.zelma4.me
```

Повинен показати твій IP сервера.

---

## Крок 2: Налаштування на сервері

### 2.1 Встановити Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx -y

# Запустити Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2.2 Скопіювати nginx конфігурацію

```bash
# Завантажити конфіг на сервер
sudo nano /etc/nginx/sites-available/bunker.zelma4.me
```

Скопіюй вміст файлу `nginx-domain.conf` з проекту.

### 2.3 Активувати конфіг

```bash
# Створити symlink
sudo ln -s /etc/nginx/sites-available/bunker.zelma4.me /etc/nginx/sites-enabled/

# Видалити default конфіг (опціонально)
sudo rm /etc/nginx/sites-enabled/default

# Перевірити конфігурацію
sudo nginx -t

# Перезапустити Nginx
sudo systemctl restart nginx
```

---

## Крок 3: Отримати безкоштовний SSL сертифікат (Let's Encrypt)

### 3.1 Встановити Certbot

```bash
# Ubuntu/Debian
sudo apt install certbot python3-certbot-nginx -y
```

### 3.2 Отримати SSL сертифікат

```bash
sudo certbot --nginx -d bunker.zelma4.me
```

Certbot запитає:
- **Email**: Введи свій email для повідомлень
- **Terms of Service**: Погодись (Y)
- **Share email**: Можна відмовитись (N)
- **Redirect HTTP to HTTPS**: Вибери 2 (рекомендовано)

### 3.3 Автоматичне оновлення сертифікату

Certbot автоматично додасть cron job для оновлення. Перевір:

```bash
sudo certbot renew --dry-run
```

---

## Крок 4: Запустити додаток на сервері

### 4.1 Використовуючи Docker (РЕКОМЕНДОВАНО)

```bash
cd bunker-game
./deploy-server.sh
```

Додаток буде працювати на `localhost:8765`, а Nginx проксує на `bunker.zelma4.me`.

### 4.2 Або без Docker (systemd)

Створи systemd service:

```bash
sudo nano /etc/systemd/system/bunker-game.service
```

Вміст:
```ini
[Unit]
Description=Bunker Game Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/bunker-game
Environment="PATH=/path/to/bunker-game/venv/bin"
ExecStart=/path/to/bunker-game/venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Запусти:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bunker-game
sudo systemctl start bunker-game
sudo systemctl status bunker-game
```

---

## Крок 5: Налаштувати Firewall

```bash
# Дозволити HTTP і HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Якщо використовуєш SSH
sudo ufw allow 22/tcp

# Активувати firewall
sudo ufw enable

# Перевірити статус
sudo ufw status
```

**ВАЖЛИВО:** Порт 8765 НЕ потрібно відкривати, бо Nginx проксує запити з 443 → 8765 локально.

---

## ✅ Перевірка

Після всіх налаштувань:

1. **Відкрий браузер**: https://bunker.zelma4.me
2. **Перевір SSL**: Має бути зелений замочок 🔒
3. **Тестування гри**: Створи кімнату та поділись посиланням

---

## 🔧 Корисні команди

### Переглянути логи Nginx
```bash
# Access logs
sudo tail -f /var/log/nginx/bunker.zelma4.me.access.log

# Error logs
sudo tail -f /var/log/nginx/bunker.zelma4.me.error.log
```

### Перезапустити сервіси
```bash
# Nginx
sudo systemctl restart nginx

# Docker додаток
cd bunker-game
docker-compose restart

# Systemd додаток
sudo systemctl restart bunker-game
```

### Перевірити статус
```bash
# Nginx
sudo systemctl status nginx

# Docker
docker-compose ps

# Systemd
sudo systemctl status bunker-game
```

### Оновити SSL сертифікат вручну
```bash
sudo certbot renew
sudo systemctl restart nginx
```

---

## 🐛 Troubleshooting

### Помилка: 502 Bad Gateway

```bash
# Перевірити чи працює додаток
curl http://localhost:8765

# Переглянути логи
sudo tail -f /var/log/nginx/bunker.zelma4.me.error.log
docker-compose logs -f  # якщо Docker
```

### Помилка: Connection refused

```bash
# Перевірити що порт 8765 слухається
sudo netstat -tulpn | grep 8765

# Або
sudo lsof -i :8765
```

### DNS не оновлюється

- Зачекай 5-30 хвилин для propagation
- Очисти DNS кеш на комп'ютері:
  ```bash
  # macOS
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  
  # Windows
  ipconfig /flushdns
  
  # Linux
  sudo systemd-resolve --flush-caches
  ```

### SSL сертифікат не створюється

```bash
# Перевірити що порт 80 відкритий
sudo ufw status

# Перевірити що домен вказує на сервер
dig bunker.zelma4.me

# Спробувати ще раз
sudo certbot --nginx -d bunker.zelma4.me --force-renewal
```

---

## 📊 Архітектура

```
Internet (HTTPS)
    ↓
bunker.zelma4.me:443 (Nginx з SSL)
    ↓
localhost:8765 (FastAPI додаток)
    ↓
SQLite Database
```

---

## 🔐 Безпека

Після налаштування рекомендую:

1. ✅ **HTTPS** - Вже налаштовано через Let's Encrypt
2. ✅ **Firewall** - Відкриті тільки 80, 443, 22
3. ⚠️ **SECRET_KEY** - Змінити в `.env` файлі:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
4. ⚠️ **Rate Limiting** - Додати nginx rate limit (опціонально)
5. ⚠️ **Backup** - Регулярно робити backup бази даних

---

## 🎉 Готово!

Тепер гравці можуть підключатись через:
- **https://bunker.zelma4.me** - Безпечне з'єднання з SSL
- Працює на всіх пристроях (комп'ютер, телефон, планшет)
- WebSocket працює через HTTPS (wss://)

**Поділись посиланням з друзями та грайте!** 🎮
