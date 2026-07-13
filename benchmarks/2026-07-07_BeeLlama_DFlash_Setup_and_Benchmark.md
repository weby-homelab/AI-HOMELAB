# 2026-07-07 | BeeLlama.cpp DFlash + TurboQuant Setup and Benchmark on WS

> **Detailed expanded report:** [`beellama_dflash_turboquant.md`](./beellama_dflash_turboquant.md)
> **Follow-up to:** [`large_moe_optimization.md`](./large_moe_optimization.md)

## Цілі
* Встановити BeeLlama.cpp (fork з DFlash + TurboQuant/TCQ) на WS
* Знайти сумісний DFlash drafter GGUF
* Налаштувати на максимально ефективну роботу
* Бенчмарк під різним контекстом

## Виконані завдання

### 1. Збірка BeeLlama.cpp
* Клон `anbeeld/beellama.cpp` (commit `85e22ea`, v0.3.1)
* CMake build з `-DGGML_CUDA_FA=ON -DGGML_CUDA_FA_ALL_QUANTS=ON` (обов'язково для TurboQuant/TCQ)
* Build успішний: `turbo2, turbo3, turbo4, turbo3_tcq, turbo2_tcq` доступні
* Бінарник: `/root/beellama.cpp/build/bin/llama-server`
* ggml version: 0.13.1

### 2. Пошук DFlash Drafter
Знайдено точний матч drafter для нашого target:
* **[`Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF`](https://huggingface.co/Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF)** (0.5B параметрів, 5.76k завантажень)
* Оригінал: [`z-lab/Qwen3.6-35B-A3B-DFlash`](https://huggingface.co/z-lab/Qwen3.6-35B-A3B-DFlash) (0.4B, 183k завантажень)
* Завантажено Q5_K_M (329 MB) на `/mnt/nvme-models/qwen36-35b-a3b-dflash-Q5_K_M.gguf`
* Сумісність: target `Qwen3.6-35B-A3B-uncensored-heretic` — fine-tune від `Qwen/Qwen3.6-35B-A3B`, архітектура ідентична (n_embd=2048, n_vocab=248320)

### 3. Бенчмарк: DFlash vs MTP під різним контекстом

| Context | MTP (q8_0) gen t/s | DFlash (q5_0/q4_1) gen t/s | Delta |
|---------|---------------------|------------------------------|-------|
| 100 tok | **42.27** | 29.88 | -29.3% |
| 3K tok | **17.97** | 12.30 | -31.6% |
| 12K tok | **7.74** | 5.80 | -25.1% |
| 24K tok | **5.90** | 4.52 | -23.4% |
| 46K tok | **3.32** | 2.62 | -21.1% |

### 4. DFlash Acceptance vs KV precision

| KV Type | Precision | Acceptance | Gen t/s (code) |
|---------|-----------|------------|----------------|
| `turbo3_tcq` | 81.56% | 25.8% | 40.87 |
| `q4_0` | 88.87% | 29.9% | **43.08** |
| `q5_0`/`q4_1` | 92.65% | **53.1%** | 39.08 |
| `q5_0`/`q4_1` (reasoning off) | — | 26.1% | 36.00 |

### 5. Фінальна конфігурація: BeeLlama + MTP + q8_0 KV

**Рішення:** DFlash програв MTP для reasoning-heavy навантаження (21-35% acceptance vs MTP's 92-100%).
- MTP built-in heads треновані разом з моделлю → 92-100% acceptance
- DFlash cross-attention від окремої 0.4B моделі → 21-53% acceptance на reasoning tasks
- CPU offload tax hurts DFlash more (більше forward passes на token)

**Фінальна конфігурація:**
```bash
# BeeLlama binary з MTP + q8_0 KV (parity з upstream + reasoning guard)
/root/beellama.cpp/build/bin/llama-server \
    -m Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-Quality.gguf \
    --spec-type draft-mtp --spec-draft-n-max 3 \
    -ngl 999 -ncmoe 28 -t 10 -Cr 0-9 -Crb 0-9 \
    -c 65536 -fa on -ctk q8_0 -ctv q8_0 \
    --metrics -np 1 -b 2048 -ub 512 \
    -fit off --no-mmap --mlock \
    --temp 0.6 --top-p 0.95 --top-k 40 \
    --chat-template-kwargs '{"preserve_thinking":true}' \
    --host 0.0.0.0 --port 8080
```

## Ключові висновки (Lessons Learned)

1. **DFlash acceptance критично залежить від KV precision:** turbo3_tcq (81%) → 25.8% acceptance → q5_0/q4_1 (93%) → 53% acceptance. Cross-attention драфтера потребує точних hidden states.

2. **Reasoning tokens вбивають DFlash acceptance:** Qwen3.6 генерує 170+ reasoning tokens для простої задачі "what is 2+2?". Ці токени високентропійні (unpredictable) → DFlash acceptance впадає до 21-35%.

3. **DFlash `--reasoning on` краще ніж `off`:** Thinking tokens дають драфтеру багатший контекст через cross-attention → 53% vs 26% acceptance. Навіть якщо think-токени самі непередбачувані, якісна cross-attention покращує overall prediction.

4. **DFlash найсильніший для structured code** (низька ентропія): z-lab бенчмарки показують 3-4x на code tasks, але reasoning-heavy workload отримує лише ~1x або уповільнення через CPU offload tax.

5. **BeeLlama value-adds навіть без DFlash:**
   * TurboQuant/TCQ типи доступні (turbo3_tcq дає 4.92x KV compression → до 128K на 11GB VRAM)
   * Reasoning loop guard (детектує зациклення reasoning у довгих сесіях)
   * CopySpec (model-free speculation через rolling-hash suffix matching)
   * Up-to-date з upstream llama.cpp

6. **CPU offload tax:** Кожен DFlash draft+verify iteration несе CPU⟷GPU communication overhead. MTP (built-in heads) має менше ітерацій на token → краще підходить для hybrid GPU/CPU split на RTX 2080 Ti 11GB.

## Дотичні файли
* Скрипт запуску: `/root/start_llama.sh` на WS
* BeeLlama binary: `/root/beellama.cpp/build/bin/llama-server`
* DFlash drafter: `/mnt/nvme-models/qwen36-35b-a3b-dflash-Q5_K_M.gguf`
* Бекап upstream: `/root/start_llama_mtp.sh.bak`
* Скрипти бенчмарку: `/tmp/bench_api.py`, `/tmp/bench_dflash.py` (на WS)

## Дані моделі
* Target: `Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-Quality.gguf` (22 GB, 35B params, 3B active MoE)
* Drafter: `Anbeeld/Qwen3.6-35B-A3B-DFlash-GGUF` Q5_K_M (329 MB, 0.5B params)
* BeeLlama.cpp: commit `85e22ea`, built 2026-07-07, CUDA 13.3.73, ggml 0.13.1

> Signed: OpenCode-on-PRXMX-01-v10.48

---

<p align="center">
  Built in Ukraine under air raid sirens &amp; blackouts ⚡<br>
  &copy; 2026 Weby Homelab
</p>
