# ✅ Швидкий чеклист для bunker.zelma4.me

## 📋 Крок за кроком

### 1️⃣ Налаштування DNS в Namecheap (5 хвилин)

1. Зайди на https://www.namecheap.com/myaccount/login/
2. Domain List → Manage (біля zelma4.me)
3. Advanced DNS → Add New Record
4. Додай:
   ```
   Type: A Record
   Host: bunker
   Value: IP_ТВОГО_СЕРВЕРА
   TTL: Automatic
   ```
5. Save All Changes ✓
6. Зачекай 5-30 хвилин для поширення DNS

**Перевірити:**
```bash
nslookup bunker.zelma4.me
# Має показати IP твого сервера
```

---

### 2️⃣ Деплой додатку на сервер (3 хвилини)

```bash
# SSH на сервер
ssh user@YOUR_SERVER_IP

# Завантажити проект
git clone https://github.com/zelma4/bunker-game
cd bunker-game

# Запустити деплой
chmod +x deploy-server.sh
./deploy-server.sh
```

**Перевірити:**
```bash
docker-compose ps
# Має показати running
curl http://localhost:8765
# Має повернути HTML
```

---

### 3️⃣ Налаштування Nginx (2 хвилини)

```bash
# На сервері в папці bunker-game
chmod +x setup-nginx.sh
./setup-nginx.sh
```

**Перевірити:**
```bash
sudo nginx -t
# Має показати successful
curl http://bunker.zelma4.me
# Має повернути HTML (якщо DNS вже поширився)
```

---

### 4️⃣ Додати HTTPS (1 хвилина)

```bash
# Встановити Certbot
sudo apt install certbot python3-certbot-nginx -y

# Отримати SSL сертифікат
sudo certbot --nginx -d bunker.zelma4.me

# Ввести email та погодитись з умовами
```

**Перевірити:**
```bash
sudo certbot certificates
# Має показати сертифікат для bunker.zelma4.me
```

---

### 5️⃣ Firewall (30 секунд)

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow 8765/tcp
sudo ufw enable
sudo ufw status
```

---

## 🎉 Готово!

Гра тепер доступна на: **https://bunker.zelma4.me**

---

## 🔧 Команди для управління

### Переглянути логи
```bash
# Додаток
docker-compose logs -f

# Nginx
sudo tail -f /var/log/nginx/bunker_access.log
sudo tail -f /var/log/nginx/bunker_error.log
```

### Перезапустити
```bash
# Додаток
docker-compose restart

# Nginx
sudo systemctl restart nginx
```

### Оновити код
```bash
git pull
docker-compose up -d --build
```

### Перевірити статус
```bash
# Додаток
docker-compose ps
curl http://localhost:8765

# Nginx
sudo nginx -t
sudo systemctl status nginx

# SSL
sudo certbot certificates
```

---

## 🐛 Проблеми?

### DNS не працює
- Зачекай 30-60 хвилин
- Перевірь A record в Namecheap
- `nslookup bunker.zelma4.me`

### Сайт не відкривається
```bash
# Перевір чи працює додаток
docker-compose ps
curl http://localhost:8765

# Перевір Nginx
sudo nginx -t
sudo systemctl status nginx

# Перевір firewall
sudo ufw status
```

### SSL не працює
```bash
# Перевір сертифікат
sudo certbot certificates

# Спробуй ще раз
sudo certbot delete --cert-name bunker.zelma4.me
sudo certbot --nginx -d bunker.zelma4.me
```

---

## 📚 Детальні інструкції

- **Повна документація**: [DOMAIN_SETUP.md](DOMAIN_SETUP.md)
- **Деплой**: [DEPLOY.md](DEPLOY.md)
- **Швидкий старт**: [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
