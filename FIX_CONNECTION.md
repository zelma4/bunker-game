# 🔥 Виправлення проблеми "Немає зв'язку"

## Проблема
Docker контейнер працює (порт 8765 відкритий всередині), але не можеш підключитисьззовні.

## Причина
Порт 8765 заблокований **файрволом** на сервері або в хмарному провайдері.

---

## ⚡ Швидке рішення

### Крок 1: Відкрити порт на сервері

```bash
# На сервері запусти:
./fix-firewall.sh
```

Або вручну:

```bash
# Для Ubuntu/Debian (UFW)
sudo ufw allow 8765/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Для CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8765/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### Крок 2: Перевірити

```bash
# Перевір що порт відкритий
sudo ufw status
# або
sudo firewall-cmd --list-all
```

Має бути:
```
8765/tcp                   ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## 🌩️ Хмарні провайдери

Якщо після відкриття порту на сервері все ще не працює, потрібно відкрити порт в **Security Group** хмарного провайдера:

### DigitalOcean Droplet
1. Зайти в **Networking** → **Firewalls**
2. Додати правило:
   - Type: **Custom**
   - Protocol: **TCP**
   - Port: **8765**
   - Sources: **All IPv4, All IPv6**

### AWS EC2
1. Зайти в **EC2** → **Security Groups**
2. Обрати Security Group твоєї інстанції
3. **Inbound Rules** → **Edit**
4. Додати правило:
   - Type: **Custom TCP**
   - Port Range: **8765**
   - Source: **0.0.0.0/0** (або **Anywhere-IPv4**)

### Google Cloud Platform
1. **VPC Network** → **Firewall Rules**
2. **Create Firewall Rule**:
   - Direction: **Ingress**
   - Targets: **All instances**
   - Source IP ranges: **0.0.0.0/0**
   - Protocols and ports: **tcp:8765**

### Azure
1. **Virtual Machines** → обрати VM
2. **Networking** → **Add inbound port rule**
3. Налаштування:
   - Service: **Custom**
   - Port: **8765**
   - Protocol: **TCP**
   - Action: **Allow**

### Hetzner Cloud
1. **Firewalls** → обрати firewall
2. **Add Rule**:
   - Direction: **In**
   - Protocol: **TCP**
   - Port: **8765**
   - Source: **Any IPv4, Any IPv6**

---

## 🧪 Перевірка після налаштування

### На сервері:
```bash
# Перевірити що додаток працює
curl http://localhost:8765

# Перевірити що порт слухається
sudo netstat -tulpn | grep 8765
# або
sudo lsof -i :8765
```

### З комп'ютера:
```bash
# Замінити YOUR_SERVER_IP на IP сервера
curl http://YOUR_SERVER_IP:8765
```

Якщо працює - побачиш HTML код сторінки.

### В браузері:
```
http://YOUR_SERVER_IP:8765
```

---

## 📊 Діагностика

### Перевірити чи працює Docker:
```bash
docker-compose ps
# Статус має бути "Up"
```

### Переглянути логи:
```bash
docker-compose logs -f
# Має показувати запити
```

### Перевірити порт на сервері:
```bash
sudo netstat -tulpn | grep 8765
# Має показати: 0.0.0.0:8765
```

### Тестувати з сервера:
```bash
curl -v http://localhost:8765
# Має повернути HTTP 200 OK
```

---

## ✅ Чек-лист

- [ ] Додаток запущений (`docker-compose ps` показує "Up")
- [ ] Порт 8765 слухається (`netstat -tulpn | grep 8765`)
- [ ] Локально працює (`curl http://localhost:8765`)
- [ ] UFW/firewalld дозволяє порт 8765
- [ ] Security Group хмарного провайдера дозволяє порт 8765
- [ ] Можна підключитись ззовні (`curl http://SERVER_IP:8765`)

---

## 🎯 Альтернатива: Використати Nginx (рекомендовано)

Замість прямого доступу на порт 8765, краще використати Nginx на порту 80/443:

```bash
# Якщо є домен
./setup-domain.sh

# Або без домену - просто nginx на порту 80
sudo apt install nginx -y

# Створити конфіг
sudo nano /etc/nginx/sites-available/bunker
```

Вміст:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/bunker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Тоді доступ буде через: `http://YOUR_SERVER_IP` (без порту!)

---

## 💡 Підсумок

**Найімовірніша причина**: Файрвол блокує порт 8765

**Рішення**: 
1. Запусти `./fix-firewall.sh` на сервері
2. Відкрий порт в Security Group хмарного провайдера
3. Або використай Nginx на порту 80 (стандартний HTTP)
