# 🛡️ Advanced Hardening: Глибока ізоляція домашньої AI-лаби

> **Мета:** Захистити вашу AI-лабораторію від загроз, які приходять з незахищених пристроїв домашньої мережі (IoT-девайси, смарт-ТВ, IP-камери), та запобігти витоку ваших API-ключів та чутливих даних.

> [!CAUTION]
> Смарт-пристрої (лампочки, розетки, пилососи, камери) є **найслабшою ланкою** домашньої мережі. Вони рідко отримують оновлення безпеки, часто мають хардкодовані паролі та відправляють телеметрію на сервери в КНР. **Ваша AI-лаба НЕ повинна ділити мережу з IoT.**

---

## 📑 Зміст

1. [Мережева ізоляція (VLAN)](#-1-мережева-ізоляція-vlan)
2. [Фаєрвол AI-сервера (nftables)](#-2-фаєрвол-ai-сервера-nftables)
3. [Docker-ізоляція LLM](#-3-docker-ізоляція-llm)
4. [Моніторинг витоку секретів (Gitleaks)](#-4-моніторинг-витоку-секретів-gitleaks)
5. [Pre-commit хуки](#-5-pre-commit-хуки)
6. [SSH Hardening](#-6-ssh-hardening)
7. [Чеклист безпеки](#-чеклист-безпеки)

---

## 🌐 1. Мережева ізоляція (VLAN)

### Чому це критично?

Типова домашня мережа — це **плоска топологія**, де всі пристрої бачать один одного:

```
❌ НЕБЕЗПЕЧНА ТОПОЛОГІЯ (Flat Network)
┌──────────────────────────────────────────────────────┐
│                 192.168.1.0/24                        │
│                                                      │
│  🧠 AI Server    📱 Телефон    💡 Smart Lamp         │
│  192.168.1.50    192.168.1.20  192.168.1.100         │
│                                                      │
│  📺 Smart TV     🤖 Robot      🔓 IP Camera          │
│  192.168.1.101   192.168.1.102 192.168.1.103         │
│                                                      │
│  ⚠️ Будь-який зламаний IoT-девайс може               │
│     атакувати AI-сервер напряму!                     │
└──────────────────────────────────────────────────────┘
```

### Рекомендована архітектура (3 VLAN)

```
✅ ЗАХИЩЕНА ТОПОЛОГІЯ (VLAN Segmentation)

┌─ VLAN 10: AI Lab (192.168.10.0/24) ─────────────────┐
│  🧠 AI Server     🖥️ Open WebUI    💾 Qdrant        │
│  192.168.10.10    192.168.10.11    192.168.10.12     │
│  🔒 Повна ізоляція від IoT                           │
└──────────────────────────────────────────────────────┘
          │ (лише HTTP/HTTPS дозволено)
          │
┌─ VLAN 20: Користувачі (192.168.20.0/24) ───────────┐
│  💻 Ваш ПК        📱 Телефон      🎮 Ігрова         │
│  192.168.20.10    192.168.20.11   192.168.20.12     │
└──────────────────────────────────────────────────────┘
          │ (жодного доступу до VLAN 10!)
          │
┌─ VLAN 30: IoT Jail (192.168.30.0/24) ──────────────┐
│  💡 Лампи    📺 TV    🤖 Пилосос    🔓 Камера       │
│  ⛔ НІЯКОГО доступу до інших VLAN                    │
│  ⛔ Доступ лише до інтернету (і то обмежений)        │
└──────────────────────────────────────────────────────┘
```

### Налаштування на роутері (приклад MikroTik)

```bash
# Створення VLAN на MikroTik (RouterOS v7)
/interface vlan
add interface=bridge1 name=vlan10-ai    vlan-id=10
add interface=bridge1 name=vlan20-users vlan-id=20
add interface=bridge1 name=vlan30-iot   vlan-id=30

# IP адреси для кожного VLAN
/ip address
add address=192.168.10.1/24 interface=vlan10-ai
add address=192.168.20.1/24 interface=vlan20-users
add address=192.168.30.1/24 interface=vlan30-iot

# Фаєрвол: IoT НЕ має доступу до AI Lab
/ip firewall filter
add chain=forward src-address=192.168.30.0/24 dst-address=192.168.10.0/24 \
    action=drop comment="Block IoT -> AI Lab"
add chain=forward src-address=192.168.30.0/24 dst-address=192.168.20.0/24 \
    action=drop comment="Block IoT -> Users"

# Дозволити користувачам доступ до Web UI AI-лаби (порт 3000)
/ip firewall filter
add chain=forward src-address=192.168.20.0/24 dst-address=192.168.10.11 \
    protocol=tcp dst-port=3000 action=accept comment="Users -> WebUI"
```

> [!TIP]
> Якщо ваш роутер **не підтримує VLAN** (більшість споживчих TP-Link/Asus), використовуйте **фізичну ізоляцію**: окремий свіч або другий порт роутера з іншою підмережею для AI-лаби.

---

## 🔥 2. Фаєрвол AI-сервера (nftables)

### Базова конфігурація для AI-сервера

Цей файл обмежує вхідні з'єднання тільки необхідними портами та блокує весь вихідний трафік від LLM-контейнерів.

```bash
#!/usr/sbin/nft -f
# /etc/nftables.conf — AI-HomeLab Hardened Firewall
# Дата: 2026-06

flush ruleset

table inet filter {
    # ──────────────────────────────────────────────
    # Вхідний трафік
    # ──────────────────────────────────────────────
    chain input {
        type filter hook input priority 0; policy drop;

        # Базові правила
        ct state established,related accept
        ct state invalid drop
        iif lo accept

        # SSH (тільки з VLAN користувачів або Tailscale)
        ip saddr 192.168.20.0/24 tcp dport 22 accept comment "SSH from Users VLAN"
        ip saddr 100.64.0.0/10  tcp dport 22 accept comment "SSH from Tailscale"

        # Open WebUI (тільки з VLAN користувачів)
        ip saddr 192.168.20.0/24 tcp dport 3000 accept comment "WebUI from Users"

        # Ollama API (тільки локальна мережа AI Lab)
        ip saddr 192.168.10.0/24 tcp dport 11434 accept comment "Ollama internal"

        # Qdrant API (тільки локальна мережа AI Lab)
        ip saddr 192.168.10.0/24 tcp dport 6333 accept comment "Qdrant internal"

        # ICMP (ping) — обмежений rate
        ip protocol icmp limit rate 5/second accept
        ip6 nexthdr icmpv6 limit rate 5/second accept

        # Логування заблокованих пакетів
        log prefix "[NFTABLES-DROP-INPUT] " flags all counter drop
    }

    # ──────────────────────────────────────────────
    # Вихідний трафік
    # ──────────────────────────────────────────────
    chain output {
        type filter hook output priority 0; policy accept;

        # Дозволити базові сервіси
        ct state established,related accept

        # DNS
        tcp dport 53 accept
        udp dport 53 accept

        # HTTP/HTTPS (для оновлень системи та pull моделей)
        tcp dport { 80, 443 } accept

        # NTP
        udp dport 123 accept

        # Tailscale
        udp dport 41641 accept
    }

    # ──────────────────────────────────────────────
    # Forward (Docker traffic)
    # ──────────────────────────────────────────────
    chain forward {
        type filter hook forward priority 0; policy drop;

        ct state established,related accept

        # Docker внутрішня мережа
        iifname "br-*" oifname "br-*" accept comment "Docker inter-container"

        # Docker → Internet (лише для pull моделей, обмежений)
        iifname "br-*" oifname != "br-*" tcp dport { 80, 443 } accept

        # Блокувати все інше від Docker
        iifname "br-*" log prefix "[NFTABLES-DROP-DOCKER] " counter drop
    }
}
```

> [!WARNING]
> Після зміни `nftables.conf` **ЗАВЖДИ** виконуйте перевірку синтаксису:
> ```bash
> nft -c -f /etc/nftables.conf && echo "✅ Синтаксис OK"
> ```
> Помилка у конфігурації може повністю заблокувати доступ до сервера!

---

## 🐳 3. Docker-ізоляція LLM

### Принцип мінімальних привілеїв

```yaml
# docker-compose.yml — Безпечна конфігурація Ollama
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ai-ollama
    restart: unless-stopped

    # 🔒 Безпека: мінімальні привілеї
    security_opt:
      - no-new-privileges:true    # Заборона ескалації привілеїв
    cap_drop:
      - ALL                       # Скинути ВСІ capabilities
    cap_add:
      - SYS_NICE                  # Тільки для пріоритету GPU
    read_only: true               # Read-only файлова система
    tmpfs:
      - /tmp:size=1G              # Тимчасовий простір у RAM

    # 🔒 Мережа: тільки внутрішня Docker-мережа
    # НЕ прокидаємо порти на хост — доступ тільки через Open WebUI
    networks:
      - ai-internal

    # 🔒 Ресурси: обмеження
    deploy:
      resources:
        limits:
          memory: 16G             # Ліміт RAM
        reservations:
          memory: 4G

    volumes:
      - ollama_models:/root/.ollama  # Моделі persistent

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: ai-webui

    # 🔒 Порт прокинутий ТІЛЬКИ на localhost
    ports:
      - "127.0.0.1:3000:8080"

    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

    environment:
      - OLLAMA_BASE_URL=http://ai-ollama:11434
      - SCARF_NO_ANALYTICS=true
      - DO_NOT_TRACK=true

    networks:
      - ai-internal

networks:
  ai-internal:
    driver: bridge
    internal: false   # false — потрібен для UI, true — для повної ізоляції
```

### Заборона вихідних з'єднань для Ollama

Якщо ваша модель вже завантажена, Ollama **не потребує інтернету**. Заблокуйте вихідні:

```bash
# Створити ізольовану мережу без доступу до інтернету
docker network create --internal ai-isolated

# Перепідключити Ollama до ізольованої мережі
docker network disconnect bridge ai-ollama
docker network connect ai-isolated ai-ollama
```

---

## 🔑 4. Моніторинг витоку секретів (Gitleaks)

### Встановлення

```bash
# Linux (amd64)
GITLEAKS_VERSION="8.22.1"
wget -qO- "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
  | tar xz -C /usr/local/bin gitleaks

# macOS
brew install gitleaks
```

### Сканування репозиторію

```bash
# Перевірити всю історію Git
gitleaks detect --source . --verbose

# Перевірити тільки staged зміни (перед комітом)
gitleaks protect --source . --staged --verbose

# Вивести звіт у JSON
gitleaks detect --source . --report-format json --report-path ./gitleaks-report.json
```

### Що Gitleaks знаходить

| Тип секрету | Приклад | Ризик |
|---|---|---|
| OpenAI API Key | `sk-proj-abc123...` | 💰 Фінансовий (необмежені витрати) |
| Anthropic Key | `sk-ant-api03-...` | 💰 Фінансовий |
| GitHub PAT | `ghp_xxxxxxxxxxxx` | 🔓 Повний доступ до репо |
| AWS Keys | `AKIA...` | 💣 Катастрофічний |
| Private Keys | `-----BEGIN RSA...` | 💣 Катастрофічний |
| Docker Hub PAT | `dckr_pat_...` | 🔓 Push доступ до образів |
| `.env` файли | `SECRET_KEY=...` | 🔓 Залежить від контексту |

> [!IMPORTANT]
> Якщо секрет **вже потрапив** у Git-історію, простого видалення файлу недостатньо! Використовуйте `git filter-repo --replace-text` для повного очищення, а потім **відкличте** скомпрометований токен на стороні провайдера.

---

## 🪝 5. Pre-commit хуки

### Налаштування `.pre-commit-config.yaml`

Помістіть цей файл у корінь вашого репозиторію:

```yaml
# .pre-commit-config.yaml
repos:
  # Gitleaks — сканування секретів
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.22.1
    hooks:
      - id: gitleaks

  # Базові перевірки
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-yaml           # Валідація YAML
      - id: check-json           # Валідація JSON
      - id: end-of-file-fixer    # Newline в кінці файлу
      - id: trailing-whitespace  # Видалення хвостових пробілів
      - id: check-added-large-files  # Блокувати великі файли
        args: ['--maxkb=1024']
      - id: detect-private-key   # Виявлення приватних ключів
      - id: check-merge-conflict # Маркери конфліктів
```

### Активація

```bash
# Встановлення pre-commit
pip install pre-commit

# Активація хуків у вашому репозиторії
cd /path/to/your/repo
pre-commit install

# Перевірка всіх файлів (одноразово)
pre-commit run --all-files
```

Тепер кожен `git commit` автоматично перевірятиме ваш код на наявність секретів!

---

## 🔐 6. SSH Hardening

### Мінімальні зміни для AI-сервера

```bash
# /etc/ssh/sshd_config.d/99-ai-homelab.conf

# Заборона входу по паролю (тільки ключі)
PasswordAuthentication no
ChallengeResponseAuthentication no

# Заборона входу під root
PermitRootLogin prohibit-password

# Тільки протокол 2
Protocol 2

# Обмеження кількості спроб
MaxAuthTries 3

# Timeout неактивних сесій (5 хвилин)
ClientAliveInterval 60
ClientAliveCountMax 5

# Заборона X11 forwarding
X11Forwarding no

# Заборона Agent forwarding (запобігає атакам через forwarded keys)
AllowAgentForwarding no

# Обмеження доступу по користувачах
AllowUsers admin

# Зміна порту (опціонально, але зменшує шум у логах)
# Port 54322
```

### Застосування

```bash
# Перевірити конфігурацію ПЕРЕД перезапуском
sshd -t && echo "✅ Конфігурація SSH валідна"

# Перезапустити SSH
sudo systemctl restart sshd
```

> [!CAUTION]
> **ЗАВЖДИ** тримайте активну SSH-сесію відкритою під час зміни конфігурації SSH. Якщо щось піде не так, ви зможете відкотити зміни через існуючу сесію.

---

## ✅ Чеклист безпеки

Використовуйте цей чеклист при первинному налаштуванні AI-лаби:

### Мережа

- [ ] AI-сервер ізольований від IoT-пристроїв (VLAN або фізично)
- [ ] Ollama API (порт 11434) **НЕ** доступний з інтернету
- [ ] Qdrant API (порт 6333) **НЕ** доступний з інтернету
- [ ] Open WebUI прив'язаний до `127.0.0.1` або захищений reverse-proxy
- [ ] Firewall (nftables) налаштований та активний
- [ ] Tailscale або WireGuard для віддаленого доступу

### Docker

- [ ] Контейнери запущені з `no-new-privileges`
- [ ] Всі capabilities скинуті (`cap_drop: ALL`)
- [ ] Порти прив'язані до `127.0.0.1`, а не `0.0.0.0`
- [ ] Телеметрія вимкнена (`DO_NOT_TRACK=true`)
- [ ] Resource limits встановлені

### Секрети

- [ ] `.env` додано до `.gitignore`
- [ ] Gitleaks встановлений та налаштований як pre-commit hook
- [ ] API-ключі передаються ТІЛЬКИ через змінні середовища
- [ ] Жодних хардкодованих паролів у коді

### SSH

- [ ] Вхід по паролю вимкнено (тільки ключі)
- [ ] Root-доступ обмежений
- [ ] Fail2ban встановлений та активний
- [ ] Нестандартний порт SSH (опціонально)

### Моделі

- [ ] Використовуються тільки верифіковані моделі (Meta, Google, Mistral, Microsoft)
- [ ] Моделі завантажені з офіційних джерел (Ollama Library, HuggingFace)
- [ ] Жодних моделей з РФ або КНР (DeepSeek, Qwen, YandexGPT)

---

> **Далі:** [SECURITY.md](../../SECURITY.md) — загальна політика безпеки проєкту
>
> **Шаблони:** [templates/](../templates/) — готовий код для розгортання агентів

---

> *AI-HomeLab — захищаємо AI-майбутнє України 🇺🇦*
