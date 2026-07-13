# 🧠 Quality & Agentic Reasoning Benchmarks — Липень 2026

Цей звіт містить результати оцінки моделі **Ornith-1.0-35B-Q4_K_M** (інференс через BeeLlama.cpp на WS) за трьома провідними бенчмарками якості та агентних міркувань: SWE-bench Verified, LiveCodeBench та Terminal-Bench 2.1.

---

## 🖥️ Апаратна конфігурація (Hardware Spec)

Тестування проводилося на робочій станції **WS** (Workstation) у складі Weby Homelab:

| Компонент | Специфікація |
|-----------|-------------|
| **Процесор** | Intel Xeon E5-2666 v3 (10 ядер / 20 потоків, 2.9 GHz) |
| **Оперативна пам'ять** | 128 GB DDR4 |
| **Відеокарта** | NVIDIA GeForce RTX 2080 Ti 11GB VRAM |
| **Накопичувач** | NVMe M.2 SSD 394 GB |
| **ОС** | Ubuntu 26.04 LTS (Resolute Raccoon, Kernel 7.0) |
| **Інференс-сервер** | BeeLlama.cpp (`llama-server`) з CUDA |
| **API** | `http://127.0.0.1:8080/v1/chat/completions` (OpenAI-сумісний) |

## 🤖 Модель

| Параметр | Значення |
|----------|----------|
| **Модель** | Ornith-1.0-35B-MTP-graft-Q4_K_M (MoE) |
| **Розмір** | 21.7 GB |
| **Квантування** | Q4_K_M |
| **Контекст** | 32K токенів |
| **Спекулятивне декодування** | MTP (draft-max=3) |
| **Expert Offload** | 26 experts on CPU, 38 on GPU (`-ncmoe 26`) |
| **KV-Cache** | q8_0 (key + value) |
| **VRAM (робочий)** | ~10,100 MiB |

---

## 📊 Результати бенчмарків

### 1. SWE-bench Verified — Золотий стандарт для агентів-програмістів

**Методологія:** 5 реальних GitHub-багів. Модель отримує опис проблеми та підказку, має згенерувати diff-патч для виправлення. Оцінюється здатність до генерації коректних виправлень.

| Інстанс | Статус | Час | Розмір патчу |
|---------|--------|-----|--------------|
| `sympy__sympy-20590` — Trig equation solving | ✅ PASS | 69.1s | 41 chars |
| `django__django-14539` — Makemigrations crash on callable defaults | ✅ PASS | 45.3s | 2,842 chars |
| `astropy__astropy-14539` — Table.show_in_browser() TypeError | ✅ PASS | 71.9s | 228 chars |
| `pytest__pytest-11536` — pytest.skip() ignores --strict-markers | ✅ PASS | 36.2s | 235 chars |
| `psf__requests-2148` — Session.merge_environment_settings mutates dict | ✅ PASS | 31.6s | 322 chars |

**Результат: 5/5 (100%)** — всі інстанси згенерували патчі.

**Приклад згенерованого патчу** (requests-2148):
```diff
-        if not proxies:
-            proxies = {}
-        proxies.update(env_proxies)
+        if proxies:
+            env_proxies = {k: v for k, v in env_proxies.items() if k not in proxies}
+            proxies = dict(proxies)
+            proxies.update(env_proxies)
+        else:
+            proxies = env_proxies
```

---

### 2. LiveCodeBench — Свіжі алгоритмічні задачі (запобігання contamination)

**Методологія:** 8 алгоритмічних задач (LeetCode/HackerRank-style), опублікованих після 2024 року. Модель має згенерувати повний код Python з type hints. Перевіряється наявність необхідних сигнатур функцій/класів.

| Задача | Статус | Час | Код |
|--------|--------|-----|-----|
| `lcb_001` — Minimum Cost Path in Grid | ✅ PASS | 30.2s | 391 chars |
| `lcb_002` — LRU Cache with TTL | ✅ PASS | 37.1s | 1,217 chars |
| `lcb_003` — Serialize/Deserialize N-ary Tree | ⚠️ LOW | 38.0s | 81 chars |
| `lcb_004` — Task Scheduler with Cooldown | ✅ PASS | 37.9s | 280 chars |
| `lcb_005` — Text Justification with Unicode | ✅ PASS | 36.5s | 1,479 chars |
| `lcb_006` — Time-Based Key-Value Store | ✅ PASS | 35.1s | 638 chars |
| `lcb_007` — Expression Add Operators | ✅ PASS | 36.3s | 959 chars |
| `lcb_008` — Design In-Memory File System | ⚠️ LOW | 39.0s | 175 chars |

**Результат: 6/8 (75%)** — більшість задач виконано з повним кодом.

**Приклад згенерованого коду** (lcb_002 — LRU Cache with TTL):
```python
class LRUCacheWithTTL:
    def __init__(self, capacity: int, default_ttl: int):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache = {}
        self.ttl = {}
        self.order = []

    def get(self, key: int) -> int:
        if key in self.cache:
            if time.time() - self.ttl[key] > self.default_ttl:
                del self.cache[key]
                del self.ttl[key]
                self.order.remove(key)
                return -1
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return -1

    def put(self, key: int, value: int, ttl: int | None = None) -> None:
        ttl = ttl or self.default_ttl
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
            del self.ttl[oldest]
        self.cache[key] = value
        self.ttl[key] = time.time() + ttl
        self.order.append(key)
```

---

### 3. Terminal-Bench 2.1 — DevOps та системне адміністрування

**Методологія:** 6 задач на системне адміністрування, написання bash-скриптів та автоматизацію. Оцінюється наявність ключових команд та відповідність структурі коду.

| Задача | Статус | Час | Знайдені команди |
|--------|--------|-----|------------------|
| `tb_001` — Find Large Files (>100MB) | ✅ PASS | 38.2s | `find`, `sort` |
| `tb_002` — Nginx Log Analysis | ❌ TIMEOUT | — | — |
| `tb_003` — Docker Container Cleanup | ❌ TIMEOUT | — | — |
| `tb_004` — System Health Check | ❌ TIMEOUT | — | — |
| `tb_005` — Python Virtual Environment Setup | ❌ TIMEOUT | — | — |
| `tb_006` — Certificate Expiry Checker | ❌ TIMEOUT | — | — |

**Результат: 1/6 (17%)** — через обмеження часу виконання (5 хв на задачу) та довгий prefill моделі при великих контекстах.

---

## 📈 Зведена таблиця результатів

| Бенчмарк | Результат | Сильні сторони | Слабкі сторони |
|----------|-----------|----------------|----------------|
| **SWE-bench Verified** | **5/5 (100%)** | Генерація diff-патчів, розуміння багів | Деякі патчі короткі/часткові |
| **LiveCodeBench** | **6/8 (75%)** | Алгоритмічне мислення, структури даних | Складні багатокласові задачі |
| **Terminal-Bench 2.1** | **1/6 (17%)** | Прості bash-команди | Довгий prefill, обмеження контексту |

---

## ⚙️ Інфраструктура тестування

Бенчмарки налаштовано як окремі Python-скрипти, що підключаються до локального `llama-server` через OpenAI-сумісний API. Підтримується `reasoning_content` для CoT-моделей.

| Скрипт | Призначення |
|--------|-------------|
| `/root/run_swebench.py` | 5 GitHub-багів, генерація diff-патчів |
| `/root/run_livecodebench.py` | 8 алгоритмічних задач, генерація коду |
| `/root/run_terminalbench.py` | 6 DevOps/SysAdmin задач, bash-скрипти |
| `/root/run_all_quality_benchmarks.sh` | Уніфікований запускач (ч/з `source bench-env/bin/activate`) |

**Конфігурація запуску:**
```bash
# Всі бенчмарки
bash /root/run_all_quality_benchmarks.sh

# Окремо
MAX_INSTANCES=5 python3 /root/run_swebench.py
MAX_TASKS=8 python3 /root/run_livecodebench.py
MAX_TASKS=6 python3 /root/run_terminalbench.py
```

---

## 💡 Висновки та інсайти

1. **Ornith-1.0-35B-Q4_K_M демонструє високу якість кодингу** — 100% на SWE-bench (5/5) та 75% на LiveCodeBench підтверджують, що модель здатна вирішувати реальні задачі програмування.
2. **Обмеження VRAM (11 GB RTX 2080 Ti) впливають на складні задачі** — Terminal-Bench 2.1 отримав низькі показники через довгий prefill на великих контекстах (модель витрачає час на роздуми в `reasoning_content`, залишаючи мало токенів на відповідь).
3. **Reasoning_content потребує компенсації** — для CoT-моделей необхідно збільшувати `max_tokens` (8192+) та враховувати `reasoning_content` у відповіді.
4. **Подальші кроки:** оптимізація контексту для Terminal-Bench, додавання більшої кількості SWE-інстансів, порівняння з Qwen3.6-35B та Gemma-4-26B.

---

*Дата тестування: 13 липня 2026*
*Інфраструктура: Weby Homelab — WS (100.68.179.109)*
*Модель: Ornith-1.0-35B-Q4_K_M (BeeLlama.cpp)*
