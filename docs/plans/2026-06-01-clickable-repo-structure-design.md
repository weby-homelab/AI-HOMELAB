# Plan: Interactive Clickable Repository Structure Redesign

- **Date:** 2026-06-01
- **Status:** Approved
- **Scope:** Rewrite the static, non-clickable repository structure code blocks in `README.md` and `README_ENG.md` into highly visible, modern, and fully clickable Markdown lists with folder/file emojis and status badges.

## Design Details

### 1. Rationale
The previous design utilized raw markdown code blocks (` ``` `) to show a folder structure. While it displayed spacing correctly, it made it impossible for users to click on folder or file links directly to navigate. Converting this section to direct Markdown using Unicode characters (`├──`, `└──`) and explicit links allows GitHub to render it as clickable text while retaining the file tree visualization.

### 2. File Targets
- [README.md](file:///root/geminicli/projects/ai/README.md) - Ukrainian version (lines 162-201)
- [README_ENG.md](file:///root/geminicli/projects/ai/README_ENG.md) - English version (lines 162-201)

### 3. Concrete Layout (Ukrainian)
```markdown
📂 [**`ai/`**](./)
├── 📁 [**`benchmarks/`**](./benchmarks/) — *Бенчмарки заліза та енергоефективність*
│   └── ⚡ [**`hardware_efficiency.md`**](./benchmarks/hardware_efficiency.md) — *GPU vs Apple Silicon (t/s/W)*
│
├── 📁 [**`configs/`**](./configs/) — *Готові Docker-compose конфігурації*
│   ├── ✅ [**`ollama/`**](./configs/ollama/) — *Ollama + Open WebUI в один клік*
│   ├── ⏳ **`vllm/`** — `(coming soon)` *vLLM для production-grade інференсу*
│   └── ⏳ **`dify/`** — `(coming soon)` *Dify AI — no-code агентна платформа*
│
├── 📁 [**`templates/`**](./templates/) — *Шаблони та приклади коду*
│   ├── 🧠 [**`langgraph_rag_agent.py`**](./templates/langgraph_rag_agent.py) — *Corrective RAG Agent (LangGraph + Qdrant)*
│   └── 🤖 [**`agent-code-cli/`**](./templates/agent-code-cli/) — *Claude Code Style Agent CLI (Ollama + Claude)*
│
├── 📁 **`projects/`** — `(coming soon)` *Ідеї та реалізації пет-проєктів*
│   ├── ⏳ **`local-osint/`** — `(coming soon)` *Локальні OSINT-помічники*
│   ├── ⏳ **`biz-automation/`** — `(coming soon)` *Автоматизатори бізнес-рутини*
│   └── ⏳ **`rag-pipeline/`** — `(coming soon)` *RAG-пайплайн по власним документам*
│
├── 📁 [**`docs/`**](./docs/) — *Документація та гайди*
│   ├── 📁 [**`research/`**](./docs/research/) — *Дослідження AI-ландшафту*
│   │   └── 🔬 [**`ai-landscape-may-2026.md`**](./docs/research/ai-landscape-may-2026.md) — *Звіт по ШІ-моделях та стеку*
│   ├── 📁 [**`setup/`**](./docs/setup/) — *Крок-за-кроком для кожної ОС*
│   │   ├── ⏱️ [**`first-model-15-min.md`**](./docs/setup/first-model-15-min.md) — *Швидкий запуск першої моделі*
│   │   └── 🔋 [**`blackout-guide.md`**](./docs/setup/blackout-guide.md) — *Гайд з енергоефективності під час блекаутів*
│   ├── ⏳ **`security/`** — `(coming soon)` *Best practices з ізоляції моделей*
│   └── ⏳ **`quantization/`** — `(coming soon)` *Гайд по квантизації (Q4/Q8/GGUF)*
│
├── 📁 [**`security/`**](./security/) — *Політики безпеки та аудити*
│   ├── 🛡️ [**`advanced_hardening.md`**](./security/advanced_hardening.md) — *Глибока ізоляція (VLAN, nftables, Gitleaks)*
│   └── ⏳ **`model-vetting.md`** — `(coming soon)` *Критерії перевірки моделей*
│
├── 📄 [**`README.md`**](./README.md) — *Цей файл (UA)*
├── 📄 [**`README_ENG.md`**](./README_ENG.md) — *English version*
├── 📄 [**`CONTRIBUTING.md`**](./CONTRIBUTING.md) — *Гайд для контриб'юторів*
├── 📄 [**`SECURITY.md`**](./SECURITY.md) — *Політика безпеки*
├── 📄 [**`LICENSE`**](./LICENSE) — *MIT ліцензія*
└── 📄 [**`ROADMAP.md`**](./ROADMAP.md) — *Дорожня карта проєкту*
```

### 4. Concrete Layout (English)
```markdown
📂 [**`ai/`**](./)
├── 📁 [**`benchmarks/`**](./benchmarks/) — *Hardware benchmarks and energy efficiency*
│   └── ⚡ [**`hardware_efficiency.md`**](./benchmarks/hardware_efficiency.md) — *GPU vs Apple Silicon (t/s/W)*
│
├── 📁 [**`configs/`**](./configs/) — *Ready-made Docker Compose configurations*
│   ├── ✅ [**`ollama/`**](./configs/ollama/) — *One-click Ollama + Open WebUI*
│   ├── ⏳ **`vllm/`** — `(coming soon)` *vLLM for production-grade inference*
│   └── ⏳ **`dify/`** — `(coming soon)` *Dify AI — no-code agent platform*
│
├── 📁 [**`templates/`**](./templates/) — *Templates and code examples*
│   ├── 🧠 [**`langgraph_rag_agent.py`**](./templates/langgraph_rag_agent.py) — *Corrective RAG Agent (LangGraph + Qdrant)*
│   └── 🤖 [**`agent-code-cli/`**](./templates/agent-code-cli/) — *Claude Code Style Agent CLI (Ollama + Claude)*
│
├── 📁 **`projects/`** — `(coming soon)` *Ideas and implementations of pet projects*
│   ├── ⏳ **`local-osint/`** — `(coming soon)` *Local OSINT assistants*
│   ├── ⏳ **`biz-automation/`** — `(coming soon)` *Business routine automation tools*
│   └── ⏳ **`rag-pipeline/`** — `(coming soon)` *RAG pipeline for custom documents*
│
├── 📁 [**`docs/`**](./docs/) — *Documentation and guides*
│   ├── 📁 [**`research/`**](./docs/research/) — *AI landscape research*
│   │   └── 🔬 [**`ai-landscape-may-2026.md`**](./docs/research/ai-landscape-may-2026.md) — *AI models and stack report*
│   ├── 📁 [**`setup/`**](./docs/setup/) — *Step-by-step guides for each OS*
│   │   ├── ⏱️ [**`first-model-15-min.md`**](./docs/setup/first-model-15-min.md) — *Quick start of the first model*
│   │   └── 🔋 [**`blackout-guide.md`**](./docs/setup/blackout-guide.md) — *Outage energy efficiency guide*
│   ├── ⏳ **`security/`** — `(coming soon)` *Best practices for model isolation*
│   └── ⏳ **`quantization/`** — `(coming soon)` *Quantization guide (Q4/Q8/GGUF)*
│
├── 📁 [**`security/`**](./security/) — *Security policies and audits*
│   ├── 🛡️ [**`advanced_hardening.md`**](./security/advanced_hardening.md) — *Deep isolation (VLAN, nftables, Gitleaks)*
│   └── ⏳ **`model-vetting.md`** — `(coming soon)` *Model vetting criteria*
│
├── 📄 [**`README.md`**](./README.md) — *Ukrainian version*
├── 📄 [**`README_ENG.md`**](./README_ENG.md) — *This file (ENG)*
├── 📄 [**`CONTRIBUTING.md`**](./CONTRIBUTING.md) — *Contributor guide*
├── 📄 [**`SECURITY.md`**](./SECURITY.md) — *Security policy*
├── 📄 [**`LICENSE`**](./LICENSE) — *MIT License*
└── 📄 [**`ROADMAP.md`**](./ROADMAP.md) — *Project roadmap*
```
