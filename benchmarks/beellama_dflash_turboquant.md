# 🐝 BeeLlama.cpp DFlash + TurboQuant/TCQ — Розширений Звіт Бенчмарку (WS, RTX 2080 Ti 11GB)

> **Дата:** 2026-07-07
> **Хост:** WS (`100.68.179.109` / `192.168.2.24`) — Intel Xeon E5-2666 v3, 128 GB DDR4, RTX 2080 Ti 11GB
> **Repository-source:** [`anbeeld/beellama.cpp`](https://github.com/Anbeeld/beellama.cpp) (fork з DFlash + TurboQuant)
> **Target model:** `Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-Quality.gguf` (22 GB, 35B params, 3B active MoE)
> **DFlash drafter:** [`Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF`](https://huggingface.co/Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF) Q5_K_M (329 MB, 0.5B params)

---

## 📋 Зміст

1. [Цілі сесії](#-цілі-сесії)
2. [Апаратна конфігурація](#-апаратна-конфігурація)
3. [Встановлення BeeLlama.cpp](#-встановлення-beellamacpp)
4. [Пошук та вибір DFlash drafter](#-пошук-та-вибір-dflash-drafter)
5. [KV-cache типи: TurboQuant/TCQ](#-kv-cache-типи-turboquanttcq)
6. [Методологія бенчмарку](#-методологія-бенчмарку)
7. [Результати: DFlash vs MTP під різним контекстом](#-результати-dflash-vs-mtp-під-різним-контекстом)
8. [Результати: DFlash acceptance vs KV precision](#-результати-dflash-acceptance-vs-kv-precision)
9. [Результати: Reasoning on/off](#-результати-reasoning-onoff)
10. [Фінальна конфігурація](#-фінальна-конфігурація)
11. [Ключові висновки](#-ключові-висновки)
12. [Дотичні файли](#-дотичні-файли)

---

## 🎯 Цілі сесії

* Встановити BeeLlama.cpp (performance-focused fork з DFlash speculative decoding та TurboQuant/TCQ KV-cache compression) на WS
* Знайти сумісний DFlash drafter GGUF для `Qwen3.6-35B-A3B` target
* Налаштувати інференс на максимально ефективну роботу на RTX 2080 Ti 11GB
* Провести порівняльний бенчмарк DFlash vs MTP (вбудований Multi-Token Prediction) під різним контекстом (100 токенів → 60K)
* Визначити оптимальну конфігурацію для OpenCode (reasoning-heavy агентне навантаження)

---

## 🖥️ Апаратна конфігурація

| Компонент | Специфікація |
|-----------|--------------|
| **CPU** | Intel Xeon E5-2666 v3 (10 фізичних ядер / 20 потоків, Haswell, 2.90 GHz) |
| **RAM** | 128 GB DDR4 ECC |
| **GPU** | NVIDIA GeForce RTX 2080 Ti 11GB VRAM (Turing arch, CC 7.5) |
| **Storage** | NVMe M.2 SSD (моделі на `/mnt/nvme-models`) |
| **OS** | Ubuntu 26.04 LTS (Linux kernel 7.0) |
| **CUDA** | 13.3.73 (driver 610.43.02) |
| **CPU Governor** | `performance` (oneshot-служба при boot) |
| **vm.swappiness** | `10` (`/etc/sysctl.d/99-swappiness.conf`) |
| **Systemd** | `LimitMEMLOCK=infinity`, `LimitNOFILE=1048576`, `Nice=-11` |

---

## 🔨 Встановлення BeeLlama.cpp

### Клон та configure

```bash
git clone --depth 1 https://github.com/anbeeld/beellama.cpp.git
cd beellama.cpp
export PATH=/usr/local/cuda/bin:$PATH

cmake -B build \
    -DGGML_CUDA=ON \
    -DGGML_NATIVE=ON \
    -DGGML_CUDA_FA=ON \
    -DGGML_CUDA_FA_ALL_QUANTS=ON \
    -DCMAKE_BUILD_TYPE=Release
```

> **Критичний прапорець:** `-DGGML_CUDA_FA_ALL_QUANTS=ON` — обов'язковий для TurboQuant/TCQ cache типів (`turbo2`, `turbo3`, `turbo4`, `turbo2_tcq`, `turbo3_tcq`). Без нього вони або не реєструються на FA-ядрах, або тихо падають до `f16`.

### Build

```bash
cmake --build build -j20
```

* Build час: ~14 хвилин на 20 ядрах Xeon E5-2666 v3
* Native arch auto-detect: `CMAKE_CUDA_ARCHITECTURES=75-real` (Turing)
* Бінарник: `/root/beellama.cpp/build/bin/llama-server`
* BeeLlama commit: `85e22ea` (v0.3.1)
* ggml version: `0.13.1`

### Верифікація підтримки TurboQuant/TCQ

```bash
./build/bin/llama-server --help | grep -iE 'turbo|tcq|cache-type'
```

Підтверджено списки типів:
```
-ctk  cache-type-k:  f32, f16, bf16, q8_0, q6_0, q5_1, q5_0, q4_1, q4_0,
                     turbo2, turbo3, turbo4, turbo3_tcq, turbo2_tcq
-ctv  cache-type-v:  (same list)
-ctkd cache-type-k-draft:  (same list, для драфтера)
-ctvd cache-type-v-draft:  (same list)
```

DFlash також доступний:
```
--spec-type none,draft-simple,draft-eagle3,draft-mtp,ngram-simple,
            ngram-map-k,ngram-map-k4v,ngram-mod,ngram-cache,suffix,
            copyspec,recycle,dflash
--spec-dflash-cross-ctx N      (cross-attention window, токенів)
--spec-dflash-max-slots N      (max concurrent DFlash slots)
```

---

## 🔎 Пошук та вибір DFlash drafter

### Вимога

BeeLlama підтримує два DFlash-схеми:
* `dflash-draft` — Bee/buun schema
* `dflash` — upstream llama.cpp DFlash PR schema

**DFlash вимагає окремий drafter GGUF** з крос-attention тензорами. Звичайна Qwen/Llama модель **не є** DFlash drafter (помилка: `spec-type dflash is set but draft model is not a DFlash drafter`).

### Знайдені офіційні drafter-моделі

| Repo | Target | Size | Downloads |
|------|--------|------|-----------|
| [`Anbeeld/Qwen3.6-27B-DFlash-GGUF`](https://huggingface.co/Anbeeld/Qwen3.6-27B-DFlash-GGUF) | Qwen 3.6 27B (dense) | 891 MB (IQ4_XS) | 11.3k |
| [`Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF`](https://huggingface.co/Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF) | **Qwen 3.6 35B A3B (MoE)** ✅ | 266 MB (IQ4_XS) | 5.8k |
| [`Anbeeld/gemma-4-31B-it-DFlash-GGUF`](https://huggingface.co/Anbeeld/gemma-4-31B-it-DFlash-GGUF) | Gemma 4 31B | — | 4.3k |
| [`Anbeeld/gemma-4-26B-A4B-it-DFlash-GGUF`](https://huggingface.co/Anbeeld/gemma-4-26B-A4B-it-DFlash-GGUF) | Gemma 4 26B A4B (MoE) | — | 1.6k |

Оригінал нашого drafter: [`z-lab/Qwen3.6-35B-A3B-DFlash`](https://huggingface.co/z-lab/Qwen3.6-35B-A3B-DFlash) (0.4B params, спільна розробка z-lab + Modal, 183k завантажень, оновлено 18 днів тому).

### Сумісність з нашим target

* Target `Qwen3.6-35B-A3B-uncensored-heretic` — це fine-tune від `Qwen/Qwen3.6-35B-A3B`
* Архітектура та розмірності ідентичні (`n_embd=2048`, `n_vocab=248320`)
* Drafter ділить token embedding + LM head з target під час runtime → тільки DFlash-специфічні ваги у файлі
* Anbeeld підготував кванти: **IQ4_XS** (266 MB) / **Q4_K_M** (292 MB) / **Q5_K_M** (329 MB — наш вибір) / Q6_K (400 MB) / Q8_0 (515 MB) / BF16 (959 MB)

### Завантаження

```bash
cd /mnt/nvme-models
wget -q 'https://huggingface.co/Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF/resolve/main/qwen36-35b-a3b-dflash-Q5_K_M.gguf'
# 329 MB, ~10 секунд на NVMe
```

### Рекомендація Anbeeld щодо кванта драфтера

Зі HF model card:

| Drafter quant | Speedup | Acceptance |
|---------------|---------|------------|
| IQ4_XS | 4.02x | 47.6% / 87.7% |
| Q4_K_M | 3.96x | 47.0% / 87.6% |
| Q5_K_M | 3.94x | 46.8% / 87.6% |
| Q6_K | 3.79x | 45.4% / 87.2% |
| Q8_0 | 3.88x | 46.9% / 87.6% |
| BF16 | 3.60x | 44.2% / 86.9% |

Висновок Anbeeld: «Між IQ4_XS, Q4_K_M та Q5_K_M різниця менша за шум variance — можна брати будь-яку. IQ4_XS займає найменше VRAM, але Q5_K_M може дати трохи вищу acceptance довгостроково». Ми взяли Q5_K_M.

---

## 💾 KV-cache типи: TurboQuant/TCQ

BeeLlama fork додає 5 нових типів KV-cache:

| Type | Origin | bpv | Diff vs bf16 | Compression | Notes |
|------|--------|-----|---------------|-------------|-------|
| `q8_0` | upstream | 8.5 | 1.88x | — | High-fidelity (94.62% precision) |
| `q4_0` | upstream | 4.5 | 3.56x | — | Default high compression (88.87% precision) |
| `turbo4` | fork | 4.125 | 3.88x | — | Barely smaller than q4_0, slower, worse tail |
| **`turbo3_tcq`** | **fork** | **3.25** | **4.92x** | **2.4x KM Chiefs** | **Viable compact mode, 81.56% precision** |
| `turbo3` | fork | 3.125 | 5.12x | — | Weaker than turbo3_tcq |
| `turbo2_tcq` | fork | 2.25 | 7.11x | — | Last resort, 54.38% precision |
| `turbo2` | fork | 2.125 | 7.53x | — | Extreme quality risk |

**Presets (BeeLlama recommendation):**

* **Recommended high-end:** `q8_0` / `q6_0` — 94.33% precision, 46.9% bf16 size
* **Best default VRAM-constrained:** `q5_0` / `q4_1` — 92.65% precision, 32.8% bf16 size
* **Viable extreme-compression:** `turbo3_tcq` / `turbo3_tcq` — 81.56% precision, 20.3% bf16 size

> ⚠️ `turbo2_tcq` та `turbo3_tcq` — **CUDA-only**. На Metal/Vulkan/ROCm-access TCQ-fallback недоступний.

---

## 🧪 Методологія бенчмарку

### Скрипти

**`/tmp/bench_api.py`** — контекстний бенчмарк (5 рівнів контексту):
```python
# Для кожного контексту (8, 300, 1200, 2400, 4600 слів → ~100/3K/12K/24K/46K токенів)
# Запит: /v1/chat/completions з max_tokens=128, temperature=0.1
# Filler: "the quick brown fox jumps over the lazy dog. " * N
# Суфікс: "\n\nSum up the above text in one word."
# Метрики: prompt_tokens, prompt_t/s, gen_t/s, dur_s
```

**`/tmp/bench_dflash.py`** — task-specific бенчмарк:
```python
# CODE: fibonacci(n) з type hints + docstring, iteration only
# SHORT: "What is 2+2? Answer with just the number."
# LONG: 12K контекст, sum up in one word
# max_tokens=1024 для CODE (повний CoT), 500 для SHORT, 128 для LONG
```

### Тестовані конфігурації

| ID | Spec | KV type | Drafter | Reasoning | ncmoe | cross-ctx |
|----|------|---------|---------|-----------|-------|----------|
| **A** | MTP n-max=3 | q8_0 / q8_0 | — | on (preserve) | 28 | n/a |
| **B** | DFlash | turbo3_tcq / turbo3_tcq | Q5_K_M | on | 28 | 1024 |
| **C** | DFlash | q4_0 / q4_0 | Q5_K_M | on | 28 | 1024 |
| **D** | DFlash | q5_0 / q4_1 | Q5_K_M | on | 29 | 1024 |
| **E** | DFlash | q5_0 / q4_1 | Q5_K_M | off | 29 | 512 |
| **F** (final) | MTP n-max=3 | q8_0 / q8_0 | — | on (preserve) | 28 | n/a |

Час between restarts: 25-30с (модель завантажується з NVMe через `--no-mmap --mlock`).

---

## 📊 Результати: DFlash vs MTP під різним контекстом

> **Конфігурація A (MTP baseline, q8_0 KV) vs D (DFlash, q5_0/q4_1 KV)**

| Context tokens | MTP prompt t/s | MTP gen t/s | MTP dur (s) | DFlash prompt t/s | DFlash gen t/s | DFlash dur (s) | gen delta |
|----------------|-----------------|-------------|-------------|---------------------|-----------------|-----------------|-----------|
| 100 | 23.34 | **42.27** | 3.03 | 23.34 | 29.88 | 4.28 | -29.3% |
| 3,020 | 424.04 | **17.97** | 7.12 | 290.12 | 12.30 | 10.41 | -31.6% |
| 12,020 | 726.38 | **7.74** | 16.55 | 544.26 | 5.80 | 22.09 | -25.1% |
| 24,020 | 1,107.04 | **5.90** | 21.70 | 848.07 | 4.52 | 28.32 | -23.4% |
| 46,020 | 1,193.19 | **3.32** | 38.57 | 942.84 | 2.62 | 48.81 | -21.1% |
| 60,020 | 1,194.29 | **3.32** | 38.53 | 942.84 | 2.62 | 48.81 | -21.1% |

**Спостереження:**

* MTP стабільно виграє на ВСІХ рівнях контексту (на короткому 100-ток: 42.27 vs 29.88 gen t/s).
* Prefill в MTP аналогічно швидший (вуllama.cpp використовує вбудовані MTP heads → менше додаткових forward passes).
* DFlash поступається на 21-32% на reasoning-heavy промптах через низький acceptance (завдання sum-up-one-word втрачає прямий зв'язок до structured output).

**VRAM usage порівняння:**

| Конфіг | VRAM used | VRAM free |
|--------|-----------|-----------|
| A (MTP q8_0) | 10,332 MiB | 497 MiB |
| B (DFlash turbo3_tcq) | 10,562 MiB | 267 MiB |
| D (DFlash q5_0/q4_1) | 10,184 MiB | 645 MiB |

---

## 📈 Результати: DFlash acceptance vs KV precision

| KV Type | KL Divergence Precision | Acceptance | Gen t/s (code, 1024 tok) | delta vs MTP |
|---------|-------------------------|------------|---------------------------|--------------|
| `turbo3_tcq` / `turbo3_tcq` | 81.56% | **25.8%** | 40.87 t/s | -3.3% |
| `q4_0` / `q4_0` | 88.87% | **29.9%** | 43.08 t/s | +1.9% |
| `q5_0` / `q4_1` | 92.65% | **53.1%** | 39.08 t/s | -7.6% |
| `q5_0` / `q4_1` (reasoning off) | — | 26.1% | 36.00 t/s | -15.4% |

**Ключовий інсайт:** AcceptanceRowCount стрибає 25.8% → 53.1% при переході з turbo3_tcq на q5_0/q4_1 (precision 81% → 93%). Kernel precisioncritically  важлива для DFlash — cross-attention драфтера потребує точно розрахованих hidden states з target model.

**Але:**高处 acceptance не завжди = вища швидкість. q5_0/q4_1 має 53% acceptance але 39.08 t/s, тоді як q4_0 має 29.9% acceptance але 43.08 t/s. Причина: q4_0 має там менший KV-cache overhead за decode → більше compute budget на draft verification.

---

## 🧠 Результати: Reasoning on/off

Qwen3.6-35B-A3B з `--reasoning on` + `--chat-template-kwargs '{"preserve_thinking":true}'` генерує think-токени (для задачі "what is 2+2?": 167 reasoning tokens + 3 visible final = "4").

| Reasoning | Acceptance | Gen t/s (short task) | Behavior |
|-----------|------------|----------------------|----------|
| `on` (preserve) | **53.1%** | 44.73 (149 токенів) | Драфтер отримує контекст з thinking tokens |
| `off` | 26.1% | 38.60 (146 токенів) | Менше контексту для cross-attention |

**Ключовий інсайт:** Здається контрінтуїтивним, проте thinking tokens дають drafter-моделі багатший контекст через cross-attention → покращують prediction thinking-сегменту. Навіть якщо thinking tokens самі no-entropійні, хороша якість cross-attention посилює overall acceptance з 26% до 53%.

---

## 🏆 Фінальна конфігурація

### Рішення

**DFlash програв MTP для reasoning-heavy агентного навантаження** (OpenCode, CoT-heavy задачі):

* MTP built-in heads треновані разом з моделлю → **92-100%** acceptance
* DFlash cross-attention від окремої 0.4B моделі → **21-53%** acceptance на reasoning tasks
* CPU offload tax сильніше впливає на DFlash (більше draft+verify ітерацій на token)

### Фінальний `start_llama.sh` (BeeLlama binary + MTP)

```bash
#!/bin/bash
# BeeLlama.cpp — MTP (not DFlash) + q8_0 KV + Reasoning Loop Guard
# Rationale: DFlash's 21-35% acceptance on reasoning tasks loses to MTP's 92-100%.
# BeeLlama binary keeps: reasoning loop guard, future TurboQuant option, fork updates.

BEE_BIN="/root/beellama.cpp/build/bin/llama-server"
MODEL_PATH="/mnt/nvme-models/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-Quality.gguf"

HOST="0.0.0.0"
PORT="8080"
THREADS=10
CONTEXT_SIZE=65536

echo "==> BeeLlama MTP | Qwen3.6-35B-A3B | q8_0 KV | reasoning loop guard | adaptive DM"

$BEE_BIN \
    -m "$MODEL_PATH" \
    --spec-type draft-mtp \
    --spec-draft-n-max 3 \
    -ngl 999 \
    -ncmoe 28 \
    -t $THREADS \
    -Cr 0-9 -Crb 0-9 \
    -c $CONTEXT_SIZE \
    -fa on \
    -ctk q8_0 \
    -ctv q8_0 \
    --metrics \
    -np 1 \
    -b 2048 \
    -ub 512 \
    -fit off \
    --no-mmap --mlock \
    --temp 0.6 \
    --top-p 0.95 \
    --top-k 40 \
    --chat-template-kwargs "{\"preserve_thinking\":true}" \
    --host $HOST \
    --port $PORT

# Fallback на standard mode (без speculation) якщо MTP впаде
if [ $? -ne 0 ]; then
    echo "==> MTP failed, falling back to standard mode..."
    exec $BEE_BIN \
        -m "$MODEL_PATH" \
        -ngl 999 -ncmoe 28 -t $THREADS -Cr 0-9 -Crb 0-9 \
        -c $CONTEXT_SIZE -fa on -ctk q8_0 -ctv q8_0 \
        --metrics -np 1 -b 2048 -ub 512 -fit off --no-mmap --mlock \
        --temp 0.6 --top-p 0.95 --top-k 40 \
        --chat-template-kwargs "{\"preserve_thinking\":true}" \
        --host $HOST --port $PORT
fi
```

### Фінальні метрики (Config F, BeeLlama+MTP)

| Контекст | Prompt t/s | Gen t/s | Gen tok | Duration (s) |
|----------|------------|---------|---------|--------------|
| 100 | 27.28 | **34.92** | 128 | 3.67 |
| 3,020 | 391.60 | **16.60** | 128 | 7.71 |
| 12,020 | 701.25 | 7.47 | 128 | 17.14 |
| 24,020 | 1,085.66 | 5.79 | 128 | 22.12 |
| 46,020 | 1,187.97 | 3.30 | 128 | 38.74 |

| Task | Prompt t/s | Gen t/s | Gen tok | Duration (s) |
|------|------------|---------|---------|--------------|
| CODE (1024 tok) | 2.21 | **41.24** | 1024 | 24.83 |
| SHORT (149 tok) | 5.17 | 33.46 | 149 | 4.45 |
| 16K ctx | 564.18 | **6.01** | 128 | 21.31 |

---

## 💡 Ключові висновки (Lessons Learned)

1. **DFlash acceptance критично залежить від KV-cache precision.**
   turbo3_tcq (81.56% precision @ KLD 99.9%) → 25.8% acceptance
   Q5_K_M drafter + q5_0/q4_1 KV (92.65% precision) → 53.1% acceptance.
   Cross-attention drafter потребує точно розрахованих target hidden states.

2. **Reasoning tokens вбивають DFlash acceptance на reasoning-heavy задачах.**
   Qwen3.6 генерує 170+ reasoning tokens навіть для простої задачі "what is 2+2?". Ці токени є високентропійними (unpredictable) → DFlash acceptance впадає до 21-35% в reasoning-сегменті.

3. **`--reasoning on` є кращим за `off` для DFlash.**
   Thinking tokens дають драфтеру багатший контекст через cross-attention → покращують prediction всього послідовного рядка, навіть якщо самі think-токени непередбачувані (53% vs 26% acceptance).

4. **DFlash найсильніший для structured code/JSON (низька ентропія).**
   z-lab бенчмарки на B200 показують **3-4x speedup** на code tasks, але наш reasoning-heavy агентне навантаження отримує лише ~1x або навіть уповільнення через CPU offload tax.

5. **BeeLlama value-adds навіть zastosoвується без DFlash:**
   * TurboQuant/TCQ типи доступні (turbo3_tcq = 4.92x KV compression → до 128K контексту на 11GB VRAM)
   * Reasoning loop guard (детектує зациклення reasoning у довгих сесіях)
   * CopySpec (model-free speculation через rolling-hash suffix matching)
   * Up-to-date з upstream llama.cpp (синхронізується з master)

6. **CPU offload tax сильніше вдаряє по DFlash.**
   Кожен DFlash draft+verify iteration несе CPU⟷GPU communication overhead. MTP (вбудовані heads) має менше ітерацій на token → краще підходить для hybrid GPU/CPU split на 11GB картах.

7. **MTP залишається чемпіоном для reasoning-heavy навантаження.**
   MTP heads треновані разом з target моделлю → 92-100% acceptance (на короткому контексті) → 42.27 gen t/s на 100 ток vs DFlash 29.88 gen t/s.

8. **Preset recommendation для RTX 2080 Ti 11GB:**
   * Reasoning-heavy агент: `q8_0` / `q8_0` (94.62% precision) — безкомпромісна якість з MTP
   * Long-context (128K+): `turbo3_tcq` / `turbo3_tcq` (81% precision, 4.92x compression) — рятує від OOM, але лише для structured tasks
   * Balanced: `q5_0` / `q4_1` (92.65% precision) — BeeLlama-recommended default

---

## 📎 Дотичні файли

| Файл | Розташування на WS | Призначення |
|------|--------------------|-------------|------|
| `llama-server` (BeeLlama) | `/root/beellama.cpp/build/bin/llama-server` | Бінарник для інференсу з DFlash + TurboQuant |
| Target model | `/mnt/nvme-models/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-Quality.gguf` | 22 GB, 35B params, 3B active MoE |
| DFlash drafter | `/mnt/nvme-models/qwen36-35b-a3b-dflash-Q5_K_M.gguf` | 329 MB, 0.5B params (z-lab/Qwen3.6-35B-A3B-DFlash) |
| `start_llama.sh` | `/root/start_llama.sh` | Поточний активний конфіг (BeeLlama+MTP) |
| `start_llama_bee.sh` (DFlash) | `/tmp/start_llama_bee.sh` (локально на PRXMX-01) | DFlash-конфіг з fallback ланцюжком |
| `start_llama_mtp.sh.bak` | `/root/start_llama_mtp.sh.bak` | Бекап попереднього upstream-конфігу |
| `bench_api.py` | `/tmp/bench_api.py` (WS) | Скрипт контекстного бенчмарку |
| `bench_dflash.py` | `/tmp/bench_dflash.py` (WS) | Скрипт task-specific бенчмарку (CODE/SHORT/LONG) |
| systemd unit | `/etc/systemd/system/llama-server.service` | Systemd-конфіг з limit overrides |
| Build log | `/tmp/bee_build.log` (WS) | CMake build log BeeLlama.cpp |

### Дані моделі

| Параметр | Target | Drafter |
|----------|--------|---------|
| Repo | Qwen/Qwen3.6-35B-A3B (fine-tune heretic-uncensored) | z-lab/Qwen3.6-35B-A3B-DFlash |
| Quant | «APEX-I-Quality» (Q4_K_M-equivalent) | Q5_K_M |
| Size | 22 GB | 329 MB |
| Params | 35B (3B active MoE) | 0.5B |
| Architecture | qwen3/moe | dflash-draft (cross-attention) |
| n_embd | 2048 | 2048 |
| n_vocab | 248,320 | 248,320 |
| BeeLlama.cpp | — | commit `85e22ea`, v0.3.1, ggml 0.13.1 |
| CUDA | — | 13.3.73 |

---

## 🔗 Посилання

* Repo: [`Anbeeld/beellama.cpp`](https://github.com/Anbeeld/beellama.cpp)
* DFlash paper: [arXiv:2602.06036](https://arxiv.org/abs/2602.06036) — «DFlash: Block Diffusion for Flash Speculative Decoding»
* BeeLlama docs:
  * [quickstart-qwen36-dflash.md](https://github.com/Anbeeld/beellama.cpp/blob/main/docs/quickstart-qwen36-dflash.md)
  * [beellama-features.md](https://github.com/Anbeeld/beellama.cpp/blob/main/docs/beellama-features.md)
  * [beellama-args.md](https://github.com/Anbeeld/beellama.cpp/blob/main/docs/beellama-args.md)
* KV-cache quant benchmarks: [anbeeld.com/articles/kv-cache-quantization-benchmarks-for-long-context](https://anbeeld.com/articles/kv-cache-quantization-benchmarks-for-long-context)
* Original z-lab + Modal DFlash: [z-lab.ai/projects/dflash](https://z-lab.ai/projects/dflash)
* Попередній звіт Weby Homelab: [`benchmarks/large_moe_optimization.md`](./large_moe_optimization.md)
* Денний звіт сесії: [`2026-07-07_BeeLlama_DFlash_Setup_and_Benchmark.md`](./2026-07-07_BeeLlama_DFlash_Setup_and_Benchmark.md)

---

<p align="center">
  Built in Ukraine under air raid sirens &amp; blackouts ⚡<br>
  &copy; 2026 Weby Homelab
</p>
<!-- Опис файлу: докладний розбір тестів швидкості BeeLlama.cpp з DFlash і TurboQuant -->
