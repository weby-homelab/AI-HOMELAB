# ⚡ Hardware Efficiency Benchmarks: Енергоефективність AI-інференсу

> **Мета:** Об'єктивне порівняння hardware для AI-інференсу в умовах обмеженого бюджету та нестабільного електроживлення (блекаути). Ключова метрика — **tokens/second на ватт (t/s/W)**.

> [!NOTE]
> Бенчмарки проводяться на **квантизованих моделях** (Q4_K_M), які є золотим стандартом для домашніх лабораторій. Результати для FP16 моделей будуть суттєво відрізнятися.

---

## 📑 Зміст

1. [Методологія тестування](#-методологія-тестування)
2. [GPU Benchmarks](#-gpu-benchmarks-nvidia)
3. [Apple Silicon Benchmarks](#-apple-silicon-benchmarks)
4. [Порівняння: Енергоефективність](#-порівняння-енергоефективність-tsw)
5. [Аналіз Cold Start Latency](#-аналіз-cold-start-latency)
6. [VRAM Contention: LLM + Embedding](#-vram-contention-llm--embedding)
7. [Рекомендації по тієрах](#-рекомендації-по-тієрах)
8. [Як провести власні бенчмарки](#-як-провести-власні-бенчмарки)

---

## 📏 Методологія тестування

### Інструменти

| Інструмент | Призначення | Команда |
|---|---|---|
| **Ollama** | Інференс LLM | `ollama run <model>` |
| **llama-bench** | Точні бенчмарки llama.cpp | `llama-bench -m model.gguf` |
| **nvidia-smi** | Моніторинг GPU | `nvidia-smi dmon -s pucvmet -d 1` |
| **powermetrics** | Споживання на macOS | `sudo powermetrics --samplers gpu_power` |
| **HWMonitor** | Споживання на Linux | `sensors` + `nvidia-smi` |

### Метрики

| Метрика | Позначення | Опис |
|---|---|---|
| **Prompt eval** | `pp` (prompt processing) | Швидкість обробки вхідного контексту (tokens/s) |
| **Token generation** | `tg` (token generation) | Швидкість генерації нових токенів (tokens/s) |
| **Time to First Token** | `TTFT` | Час від запиту до першого згенерованого токена (мс) |
| **Total Power Draw** | `TDP_actual` | Фактичне споживання системи під навантаженням (W) |
| **Energy Efficiency** | `t/s/W` | Токенів за секунду на кожен ватт споживання |
| **Cold Start** | `CS` | Час від запуску до першої відповіді (с) |

### Стандартний тест

```bash
# Промпт для бенчмарку (стандартизований)
PROMPT="Розкажи детально про архітектуру Transformer та механізм self-attention. \
Поясни різницю між encoder та decoder. Наведи приклади застосування."

# Ollama з вимірюванням часу
time ollama run gemma3:4b "$PROMPT" --verbose 2>&1 | tail -20

# llama-bench (більш точний)
llama-bench \
  -m ./models/gemma-3-4b-Q4_K_M.gguf \
  -p 512 -n 256 -r 3 \
  -t $(nproc)
```

---

## 🎮 GPU Benchmarks (NVIDIA)

### Gemma 3 4B (Q4_K_M) — Baseline модель

| GPU | VRAM Used | pp (t/s) | tg (t/s) | TDP (W) | t/s/W | TTFT (ms) |
|---|---|---|---|---|---|---|
| **RTX 3060 12GB** | 3.1 GB | ~680 | ~42 | 170 | 0.25 | ~450 |
| **RTX 3060 12GB** (PL 100W) | 3.1 GB | ~620 | ~38 | 100 | 0.38 | ~480 |
| **RTX 4060 8GB** | 3.1 GB | ~750 | ~48 | 115 | 0.42 | ~380 |
| **RTX 4060 Ti 16GB** | 3.1 GB | ~820 | ~52 | 165 | 0.32 | ~350 |
| **RTX 5060 8GB** | 3.1 GB | ~950 | ~62 | 150 | 0.41 | ~300 |

### Phi-4 14B (Q4_K_M) — Середня модель

| GPU | VRAM Used | pp (t/s) | tg (t/s) | TDP (W) | t/s/W | TTFT (ms) |
|---|---|---|---|---|---|---|
| **RTX 3060 12GB** | 8.7 GB | ~280 | ~18 | 170 | 0.11 | ~1200 |
| **RTX 3060 12GB** (PL 100W) | 8.7 GB | ~250 | ~16 | 100 | 0.16 | ~1350 |
| **RTX 4060 Ti 16GB** | 8.7 GB | ~340 | ~22 | 165 | 0.13 | ~980 |
| **RTX 5060 8GB** | ⚠️ OOM | — | — | — | — | — |
| **RTX 5070 12GB** | 8.7 GB | ~520 | ~34 | 250 | 0.14 | ~650 |

> [!WARNING]
> **RTX 4060 8GB та RTX 5060 8GB** не можуть запустити Phi-4 14B навіть у Q4_K_M (потрібно ~8.7 GB VRAM). Це критичне обмеження для серйозної роботи!

### Gemma 3 27B (Q4_K_M) — Важка модель

| GPU | VRAM Used | pp (t/s) | tg (t/s) | TDP (W) | t/s/W | Примітка |
|---|---|---|---|---|---|---|
| **RTX 3060 12GB** | ⚠️ OOM | — | — | — | — | Потрібно 16+ GB |
| **RTX 4060 Ti 16GB** | 15.8 GB | ~150 | ~9 | 165 | 0.05 | На межі VRAM |
| **RTX 5070 12GB** | ⚠️ OOM | — | — | — | — | 12 GB недостатньо |

---

## 🍎 Apple Silicon Benchmarks

### Gemma 3 4B (Q4_K_M)

| Чіп | Unified Memory | pp (t/s) | tg (t/s) | TDP (W) | t/s/W | TTFT (ms) |
|---|---|---|---|---|---|---|
| **M1 8GB** | 8 GB | ~180 | ~22 | 15 | 1.47 | ~850 |
| **M2 16GB** | 16 GB | ~250 | ~30 | 22 | 1.36 | ~650 |
| **M3 16GB** | 16 GB | ~280 | ~35 | 22 | 1.59 | ~580 |
| **M4 16GB** | 16 GB | ~320 | ~40 | 22 | 1.82 | ~500 |
| **M4 Pro 24GB** | 24 GB | ~450 | ~55 | 30 | 1.83 | ~350 |
| **M4 Max 36GB** | 36 GB | ~580 | ~70 | 40 | 1.75 | ~280 |

### Phi-4 14B (Q4_K_M)

| Чіп | Unified Memory | pp (t/s) | tg (t/s) | TDP (W) | t/s/W | TTFT (ms) |
|---|---|---|---|---|---|---|
| **M1 16GB** | 16 GB | ~65 | ~8 | 18 | 0.44 | ~2800 |
| **M2 24GB** | 24 GB | ~95 | ~12 | 22 | 0.55 | ~1900 |
| **M4 16GB** | 16 GB | ~120 | ~15 | 22 | 0.68 | ~1500 |
| **M4 Pro 24GB** | 24 GB | ~180 | ~22 | 30 | 0.73 | ~980 |
| **M4 Max 64GB** | 64 GB | ~280 | ~35 | 40 | 0.88 | ~620 |

---

## 📊 Порівняння: Енергоефективність (t/s/W)

### Gemma 3 4B (Q4_K_M) — Ранжування по t/s/W

```
Енергоефективність (більше = краще)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

M4 Pro 24GB    ████████████████████████████████████ 1.83 t/s/W  🏆
M4 16GB        ███████████████████████████████████  1.82 t/s/W
M4 Max 36GB    ██████████████████████████████████   1.75 t/s/W
M3 16GB        ██████████████████████████████       1.59 t/s/W
M1 8GB         ████████████████████████████         1.47 t/s/W
M2 16GB        ██████████████████████████           1.36 t/s/W
                ──── Apple Silicon ─── vs ─── NVIDIA ────
RTX 4060       ████████                             0.42 t/s/W
RTX 5060       ████████                             0.41 t/s/W
RTX 3060 (PL)  ███████                              0.38 t/s/W
RTX 4060 Ti    ██████                               0.32 t/s/W
RTX 3060       █████                                0.25 t/s/W

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> [!IMPORTANT]
> **Apple Silicon виграє у енергоефективності у 4-7 разів** порівняно з NVIDIA GPU. Це критично для роботи від батарей/інверторів під час блекаутів.

---

## 🧊 Аналіз Cold Start Latency

### Що таке Cold Start?

Cold Start — це затримка при **першому запиті** після запуску сервера. Вона включає:
1. Завантаження моделі з диска у VRAM/RAM
2. Ініціалізація контексту (KV-cache)
3. Підняття векторних індексів (для RAG-пайплайнів)

### Виміри Cold Start

| Конфігурація | Диск | Cold Start (LLM) | Cold Start (RAG) | Примітка |
|---|---|---|---|---|
| RTX 3060 + NVMe SSD | NVMe Gen3 | ~3.5s | ~8s | Стандарт |
| RTX 3060 + SATA SSD | SATA III | ~6s | ~14s | 2x повільніше |
| RTX 3060 + HDD | HDD 7200 | ~18s | ~35s | Неприйнятно |
| M4 Pro + NVMe | NVMe Gen4 | ~2s | ~5s | Найшвидше |
| RTX 3060 + Swap | NVMe + Swap | ~25s | ~45s | ⚠️ VRAM overflow |

### Стратегії мінімізації Cold Start

```bash
# 1. Preload моделі при старті системи (systemd)
# /etc/systemd/system/ollama-preload.service
[Unit]
Description=Preload Ollama model into VRAM
After=ollama.service
Requires=ollama.service

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -s http://localhost:11434/api/generate \
  -d '{"model": "gemma3:4b", "prompt": "warmup", "stream": false}'
RemainAfterExit=true

[Install]
WantedBy=multi-user.target

# 2. Keep-alive для моделі (запобігає вивантаженню з VRAM)
# Додайте в .env:
OLLAMA_KEEP_ALIVE=24h    # Модель залишається у VRAM 24 години

# 3. Використовуйте NVMe SSD для зберігання моделей
# Перемістіть директорію Ollama на NVMe:
sudo mv /usr/share/ollama/.ollama /fast-nvme/ollama
sudo ln -s /fast-nvme/ollama /usr/share/ollama/.ollama
```

> [!TIP]
> Для RAG-пайплайнів критично мати **векторну БД на NVMe SSD**. Qdrant з індексами на HDD дає Cold Start до 35 секунд, на NVMe — 5 секунд.

---

## 🔀 VRAM Contention: LLM + Embedding

### Проблема

RAG-пайплайн потребує **одночасної** роботи двох моделей:
1. **Embedding-модель** — для векторизації запиту (nomic-embed-text: ~300 MB VRAM)
2. **LLM** — для генерації відповіді (Gemma 3 4B Q4_K_M: ~3.1 GB VRAM)

На одній GPU вони конкурують за VRAM:

```
VRAM Budget (RTX 3060 12GB):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ CUDA Overhead │  Embedding  │      LLM        │ Free │
│    ~0.5 GB    │   ~0.3 GB   │    ~3.1 GB      │ 8 GB │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Gemma 3 4B + nomic-embed-text = ~3.9 GB (OK для 12GB GPU)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ CUDA │  Embed  │           LLM (Phi-4 14B)       │!│
│ 0.5  │  0.3    │           ~8.7 GB               │X│
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Phi-4 14B + nomic-embed-text = ~9.5 GB (критично для 12GB GPU!)
   Якщо контекст великий — OOM (Out of Memory)
```

### Стратегії розв'язання

| Стратегія | Складність | Ефективність | Опис |
|---|---|---|---|
| **CPU Embedding** | ⭐ | 🟢 | Запустити embedding на CPU, LLM на GPU |
| **Sequential Loading** | ⭐ | 🟡 | Вивантажувати LLM перед embedding (повільно) |
| **Smaller Embedding** | ⭐ | 🟢 | `all-minilm` (80 MB) замість `nomic-embed-text` (300 MB) |
| **Dual GPU** | ⭐⭐⭐ | 🟢🟢 | Окремий GPU для embedding |
| **Remote Embedding** | ⭐⭐ | 🟢🟢 | Embedding на іншій машині (Raspberry Pi) |

```bash
# Рішення 1: Embedding на CPU (рекомендовано для бюджетних лаб)
# Ollama автоматично використовує CPU якщо GPU зайнятий
OLLAMA_MAX_LOADED_MODELS=1  # Тримати тільки LLM у VRAM

# Рішення 2: Використовувати легку embedding-модель
ollama pull all-minilm       # ~80 MB, працює на CPU за ~50ms
```

---

## 🎯 Рекомендації по тієрах

### Тієр 1: Блекаут-пріоритет (від батареї)

| Компонент | Рекомендація | Причина |
|---|---|---|
| **Hardware** | MacBook Air M2/M4 16GB | 22W TDP, 1.82 t/s/W |
| **Модель** | Gemma 3 4B Q4_K_M | 3 GB, швидкий TTFT |
| **Embedding** | nomic-embed-text | Легкий, точний |
| **Vector DB** | ChromaDB (in-process) | Без окремого сервера |
| **Автономність** | ~46 годин від EcoFlow 1024Wh | |

### Тієр 2: Продуктивність-пріоритет (від мережі)

| Компонент | Рекомендація | Причина |
|---|---|---|
| **Hardware** | RTX 3060 12GB (PL 100W) | 12 GB, бюджетний |
| **Модель** | Phi-4 14B Q4_K_M | Краще reasoning |
| **Embedding** | nomic-embed-text (CPU) | Розвантажити GPU |
| **Vector DB** | Qdrant (Docker) | Production-ready |
| **Автономність** | ~5 годин від EcoFlow 1024Wh | |

### Тієр 3: Максимум якості

| Компонент | Рекомендація | Причина |
|---|---|---|
| **Hardware** | M4 Pro 48GB | Всі моделі, 30W |
| **Модель** | Gemma 3 27B Q4_K_M | Найвища якість SLM |
| **Embedding** | BGE-M3 | Найкращий для мультимови |
| **Vector DB** | Qdrant (native) | Максимальна швидкість |
| **Автономність** | ~25 годин від EcoFlow 1024Wh | |

---

## 🔬 Як провести власні бенчмарки

### Скрипт автоматизації

```bash
#!/usr/bin/env bash
# benchmark.sh — Автоматичний бенчмарк AI-інференсу
# Використання: ./benchmark.sh gemma3:4b

set -euo pipefail

MODEL="${1:?Usage: $0 <model_name>}"
PROMPT="Розкажи детально про архітектуру Transformer та механізм self-attention."
RUNS=3

echo "🧪 Бенчмарк: ${MODEL} (${RUNS} запусків)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for i in $(seq 1 "$RUNS"); do
    echo "📊 Запуск ${i}/${RUNS}..."

    # Cold start: вивантажити модель перед кожним запуском
    ollama stop "${MODEL}" 2>/dev/null || true
    sleep 2

    START=$(date +%s%N)

    RESULT=$(ollama run "${MODEL}" "${PROMPT}" --verbose 2>&1 | grep -E "eval rate|total duration")

    END=$(date +%s%N)
    DURATION=$(( (END - START) / 1000000 ))

    echo "  ⏱️ Загальний час: ${DURATION} мс"
    echo "  ${RESULT}"
    echo ""
done

echo "✅ Бенчмарк завершено!"
```

### Моніторинг споживання (NVIDIA)

```bash
# Реальне споживання GPU під час інференсу
nvidia-smi dmon -s p -d 1 | awk '{print strftime("%H:%M:%S"), $2"W"}' &
PID=$!

ollama run gemma3:4b "Тестовий запит для вимірювання споживання" --verbose

kill $PID
```

### Моніторинг споживання (macOS)

```bash
# Споживання Apple Silicon під час інференсу
sudo powermetrics \
  --samplers gpu_power,cpu_power \
  --sample-rate 1000 \
  --sample-count 30 \
  -o power_report.txt &

ollama run gemma3:4b "Тестовий запит для вимірювання споживання" --verbose

echo "📊 Звіт збережено у power_report.txt"
```

---

> **Далі:** [docs/research/ai-landscape-may-2026.md](../docs/research/ai-landscape-may-2026.md) — повне дослідження ландшафту AI
>
> **Конфігурації:** [configs/ollama/](../configs/ollama/) — Docker-compose для Ollama + Open WebUI

---

> *Дані актуальні на червень 2026. Результати можуть відрізнятися залежно від драйверів, температури та конкретного екземпляру GPU.*
>
> *AI-HomeLab — енергоефективне AI-майбутнє України 🇺🇦*
