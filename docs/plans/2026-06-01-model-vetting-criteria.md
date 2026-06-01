# Model Vetting Criteria Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deeply analyze model-vetting.md (model vetting criteria) under local HomeLab sovereignty and energy constraints (June 2026), create `docs/security/model-vetting.md`, update project READMEs, and verify all relative links and formatting.

**Architecture:** Create a comprehensive, sovereign, security-first model vetting guide in Ukrainian covering geopolitical hygiene, data privacy, weight formats/integrity, resource efficiency, and licensing. Update the main README.md and English README_ENG.md to link the newly added file, changing status from "coming soon" to "completed". Run a validation script to verify link validity.

**Tech Stack:** Markdown (GitHub Flavored), Bash, Git, Python (for link validation check).

---

### Task 1: Create Model Vetting Guide

**Files:**
- Create: `docs/security/model-vetting.md`

**Step 1: Write the content draft**
Draft the criteria in `/root/geminicli/projects/ai/docs/security/model-vetting.md` including sections on:
1. Geopolitical Vetting (Filtering out entities from high-risk regions: RF/PRC, including DeepSeek and Qwen).
2. Data Privacy & Isolation (Local inference, outbound firewall filters, telemetry protection).
3. Code & Weight Integrity (GGUF formats vs pickle vulnerabilities, hash/checksum checks).
4. Performance & Efficiency (Tokens per second per Watt, memory mapping, EcoFlow/blackout limits).
5. Licensing & Compliance (Permissive open-weights licensing: LLaMA 3, Gemma, Apache 2.0).

**Step 2: Save the file**
Write code content to the file.

**Step 3: Commit**
Add and commit `docs/security/model-vetting.md`.

---

### Task 2: Update README.md and README_ENG.md

**Files:**
- Modify: `README.md`
- Modify: `README_ENG.md`

**Step 1: Update README.md**
Change `model-vetting.md` status from `⏳ coming soon` to `✅ Готово` and replace the placeholder text with actual links and descriptions.

**Step 2: Update README_ENG.md**
Change `model-vetting.md` status from `⏳ coming soon` to `✅ Done` and replace the placeholder text with actual links and English descriptions.

**Step 3: Commit**
Add and commit both updated README files.

---

### Task 3: Validate and Merge

**Files:**
- Create: `scripts/verify_links.py`

**Step 1: Write link validation script**
Create a Python script that parses `README.md`, `README_ENG.md`, and `docs/security/model-vetting.md` and checks that all local relative links (`./docs/security/model-vetting.md` etc.) point to existing files.

**Step 2: Run verification script**
Run: `python3 scripts/verify_links.py`
Expected: Output showing all verified files/links are valid with exit code 0.

**Step 3: Create GitHub Issue, Branch, and PR**
Run commands to:
1. Create a GitHub Issue "Create Model Vetting Criteria Document and Update READMEs".
2. Create branch `feature/add-model-vetting-criteria`.
3. Commit all changes under this branch.
4. Push and open a PR.
5. Merge the PR automatically using `gh pr merge --auto`.
