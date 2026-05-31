# 🧠 Ollama + Open WebUI — Локальна ШІ-лабораторія

Готова конфігурація для розгортання повноцінної локальної ШІ-лабораторії з [Ollama](https://ollama.com) та [Open WebUI](https://github.com/open-webui/open-webui) в один клік.

## ⚡ Швидкий старт

### 1. Підготовка

```bash
cd configs/ollama

# Створити .env з шаблону
cp .env.example .env

# Згенерувати секретний ключ
sed -i "s/CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32/$(openssl rand -hex 32)/" .env
```

### 2. Запуск

**CPU-only** (без відеокарти):
```bash
docker compose up -d
```

**З GPU Nvidia** (потрібен [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)):
```bash
docker compose --profile gpu up -d
```

### 3. Завантажити модель

```bash
# Легка модель (~4GB)
docker exec ai-ollama ollama pull gemma3:4b

# Потужніша (~8GB, потрібна GPU або 16GB RAM)
docker exec ai-ollama ollama pull llama3.3:8b
```

### 4. Відкрити інтерфейс

Перейдіть у браузері: **http://localhost:3000**

При першому вході створіть обліковий запис — він стане адміністратором.

---

## 📋 Вимоги

| Режим | RAM | GPU | Диск |
|---|---|---|---|
| CPU-only (4B модель) | 8 GB | — | 10 GB |
| CPU-only (8B модель) | 16 GB | — | 15 GB |
| GPU (8B модель) | 8 GB | 8 GB VRAM | 15 GB |
| GPU (14B модель) | 16 GB | 12+ GB VRAM | 25 GB |

**Програмне забезпечення:**
- Docker Engine 24+ та Docker Compose V2
- (Опціонально) NVIDIA Container Toolkit для GPU

---

## ⚙️ Конфігурація

Усі налаштування керуються через `.env` файл:

| Змінна | За замовчуванням | Опис |
|---|---|---|
| `TZ` | `Europe/Kyiv` | Часовий пояс |
| `WEBUI_SECRET_KEY` | _(обов'язково)_ | Секретний ключ для сесій |
| `WEBUI_HOST` | `127.0.0.1` | Хост прослуховування |
| `WEBUI_PORT` | `3000` | Порт веб-інтерфейсу |
| `WEBUI_AUTH` | `true` | Увімкнути авторизацію |
| `OLLAMA_NUM_PARALLEL` | `2` | Паралельні запити |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Моделей у пам'яті |
| `OLLAMA_GPU_MEMORY` | `0` (авто) | Ліміт VRAM (байти) |

> [!CAUTION]
> **`WEBUI_HOST=0.0.0.0`** відкриває доступ з усієї мережі. Використовуйте тільки за reverse proxy (Nginx/Caddy) або у довіреній мережі.

---

## 🔋 Робота від інвертора / EcoFlow

Для мінімізації споживання під час блекауту:

```bash
# В .env змініть:
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1

# Використовуйте легку модель:
docker exec ai-ollama ollama pull gemma3:4b
```

Типове споживання: **~40W** (CPU) / **~120W** (GPU).

---

## 🛑 Зупинка

```bash
docker compose down          # Зупинити (дані збережено)
docker compose down -v       # Зупинити + ВИДАЛИТИ дані
```

---

## 🔍 Діагностика

```bash
# Статус контейнерів
docker compose ps

# Логи Ollama
docker compose logs ollama-cpu -f

# Логи Open WebUI
docker compose logs open-webui -f

# Перевірити здоров'я
docker inspect ai-ollama --format='{{.State.Health.Status}}'
docker inspect ai-webui --format='{{.State.Health.Status}}'
```
