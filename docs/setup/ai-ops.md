# 📊 AI Ops: Моніторинг та обсервабільність локального ШІ

Домашня AI-лабораторія часто починається з принципу "воно працює". Проте для стабільної експлуатації, оптимізації споживання енергії під час блекаутів та розуміння реальної ефективності агентів потрібен перехід до концепції **AI Ops (Operations)**.

Цей документ описує, як налаштувати моніторинг апаратного забезпечення (GPU, CPU, енергоспоживання), метрик інференсу (Tokens/sec, TTFT) та логування кроків автономних агентів.

---

## 📑 Зміст
1. [Моніторинг заліза: GPU & Power Draw](#-1-моніторинг-заліза-gpu--power-draw)
2. [Метрики інференсу: Ollama & vLLM](#-2-метрики-інференсу-ollama--vllm)
3. [Трейсинг агентів: Langfuse & LiteLLM](#-3-трейсинг-агентів-langfuse--litellm)
4. [Еталонний стек моніторингу (Docker Compose)](#-4-еталонний-стек-моніторингу-docker-compose)

---

## 🔌 1. Моніторинг заліза: GPU & Power Draw

Для розуміння стану вашого хоста (особливо під час роботи від акумулятора) критично бачити реальне споживання енергії та температуру GPU/CPU.

### Апаратний рівень (Nvidia GPU)
Стандартна утиліта `nvidia-smi` дає миттєвий знімок стану. Але для збору метрик у часі використовується **DCGM Exporter** (офіційний експортер від Nvidia для Prometheus) або легший **nvidia-gpu-exporter**.

**Ключові метрики для відстеження:**
* `container_gpu_utilization` — завантаження графічного ядра (%)
* `container_gpu_memory_used_bytes` — споживання відеопам'яті (VRAM)
* `container_gpu_power_usage_watts` — фактичне енергоспоживання (W)
* `container_gpu_temperature_celsius` — температура GPU (критично для закритих homelab корпусів)

---

## 🧠 2. Метрики інференсу: Ollama & vLLM

Швидкість відповіді ШІ-моделей вимірюється не в гігабайтах, а в токенах.

### Ollama Prometheus Metrics
Ollama за замовчуванням має вбудований експортер Prometheus, який працює на стандартному порті.
* **Ендпоінт:** `http://localhost:11434/metrics`

Він надає метрики щодо:
* Кількості завантажених моделей у VRAM.
* Загального часу інференсу (`ollama_prompt_eval_duration_seconds`, `ollama_eval_duration_seconds`).
* Кількості оброблених токенів.

### vLLM Prometheus Metrics
Якщо ви використовуєте vLLM для важких моделей, він автоматично відкриває порт моніторингу.
* **Ендпоінт:** `http://localhost:8000/metrics`

**Ключові метрики vLLM:**
* `vllm:num_requests_waiting` — кількість запитів у черзі (показує перевантаження черги інференсу).
* `vllm:gpu_cache_usage_factor` — завантаження KV-cache відеопам'яті (якщо наближається до 1.0, можливий OOM).
* `vllm:prompt_tokens_per_second` та `vllm:generation_tokens_per_second` — реальна швидкість обробки та генерації.

---

## 🕵️ 3. Трейсинг агентів: Langfuse & LiteLLM

Коли працюють автономні агенти (наприклад, циклічні графи в LangGraph), звичайних консольних логів недостатньо. Потрібно бачити повний шлях запиту: які інструменти викликалися, скільки токенів витрачено, яка латентність кожного кроку.

Для цього використовується **Langfuse** — open-source платформа для трейсингу та аналітики ШІ-додатків.

```
┌────────────────────────────────────────────────────────┐
│                        Langfuse                        │
│                                                        │
│  [Запит користувача]                                   │
│         │                                              │
│         ▼                                              │
│  [Агент: Маршрутизатор] (350 ms, 120 tokens)           │
│         │                                              │
│         ├─► [Виклик інструменту: DB Search] (1.2s)      │
│         │                                              │
│         ▼                                              │
│  [Агент: Генератор] (850 ms, 450 tokens)               │
│         │                                              │
│         ▼                                              │
│  [Фінальна відповідь] (Сумарна вартість: $0.0004)       │
└────────────────────────────────────────────────────────┘
```

### Інтеграція LiteLLM + Langfuse
LiteLLM має вбудовану підтримку логування в Langfuse. Достатньо додати змінні середовища до конфігурації LiteLLM:

```yaml
# Додати у docker-compose або .env для LiteLLM
environment:
  - LITELLM_LOGGING_TO_LANGFUSE=True
  - LANGFUSE_PUBLIC_KEY=pk-lf-...
  - LANGFUSE_SECRET_KEY=sk-lf-...
  - LANGFUSE_HOST=http://langfuse-server:3000
```
Після цього кожен запит через проксі LiteLLM автоматично з'явиться в панелі моніторингу Langfuse з детальним аналізом латентності та токенів.

---

## 🐳 4. Еталонний стек моніторингу (Docker Compose)

Нижче наведено конфігурацію Docker Compose для швидкого розгортання повної інфраструктури моніторингу (Prometheus + Grafana + GPU Exporter) на вашому AI-сервері.

```yaml
# configs/monitoring/docker-compose.yml
version: '3.8'

services:
  # 1. Prometheus для збору метрик
  prometheus:
    image: prom/prometheus:latest
    container_name: monitoring-prometheus
    volumes:
      - prometheus-data:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    restart: unless-stopped

  # 2. Grafana для візуалізації
  grafana:
    image: grafana/grafana:latest
    container_name: monitoring-grafana
    ports:
      - "3001:3000" # Порт 3000 часто зайнятий Open WebUI
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin-secure-pass # Змініть перед запуском!
    restart: unless-stopped

  # 3. Nvidia GPU Exporter (тільки для хостів із Nvidia GPU)
  nvidia-exporter:
    image: utkuozdemir/nvidia_gpu_exporter:v1.2.0
    container_name: monitoring-nvidia-exporter
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    # Потрібно встановити nvidia-container-toolkit на хості
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ports:
      - "9835:9835"
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

### Конфігурація Prometheus (`prometheus.yml`)

Створіть файл конфігурації поруч із `docker-compose.yml`:

```yaml
global:
  scrape_interval: 5s # Часто для швидкого реагування на GPU спайки

scrape_configs:
  # Метрики хоста та GPU
  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['nvidia-exporter:9835']

  # Метрики Ollama
  - job_name: 'ollama'
    static_configs:
      - targets: ['host.docker.internal:11434'] # Доступ до хоста з Docker-мережі
```

---

## 📈 Результат
Після налаштування ви отримаєте можливість:
1. **Бачити реальне споживання енергії (Watts):** дозволяє оцінити час автономної роботи домашньої лаби від EcoFlow.
2. **Оптимізувати VRAM:** виявляти конфлікти відеопам'яті (VRAM Contention) між LLM та Embedding моделями.
3. **Аудіювати агентів:** відстежувати "нескінченні цикли" в автономних агентах, які можуть швидко розрядити вашу зарядну станцію.
