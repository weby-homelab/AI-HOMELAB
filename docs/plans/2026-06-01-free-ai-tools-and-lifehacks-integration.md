# Plan: Free AI Tools & Lifehacks Integration (June 2026)

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate the June 2026 AI tools stack (Cursor, Google AI Studio, ElevenLabs, n8n, etc.) and 7 AI lifehacks (CoVe, NotebookLM RAG, Parallel Prompting, etc.) into the AI-HomeLab repository in both Ukrainian and English, strictly aligning the "Local-first AI" recommendation with Principle 1 (Technological Hygiene).

**Architecture:** Create two dedicated documentation guides (`docs/research/free-ai-tools-lifehacks.md` in UA, and `docs/research/free-ai-tools-lifehacks_ENG.md` in ENG) containing a deep analysis of each tool and hack, explicitly explaining how the Local-first AI tip complies with the project's zero-PRC-weight policy. Update both `README.md` and `README_ENG.md` trees and modules tables to link to these new files.

**Tech Stack:** Markdown, Git, GPG signatures.

---

### Task 1: Create Ukrainian Free AI Tools & Lifehacks Guide

**Files:**
- Create: `docs/research/free-ai-tools-lifehacks.md`

**Step 1: Write the guide**
Write the comprehensive guide in Ukrainian, covering:
1. Cursor, Google AI Studio, Canva Magic Studio, Krea.ai, Higgsfield / getimg.ai, ElevenLabs, n8n (self-hosted), Obsidian + AI.
2. The 7 lifehacks, highlighting Principle 1 for the Local-first AI hack (strictly Meta LLaMA 4, Mistral, Google Gemma 3/4, Microsoft Phi-4; no Qwen/DeepSeek).
3. Include clear markdown headings, tables, tip boxes, and links to official tools.

**Step 2: Run verification**
Verify the file exists and is not empty.
Run: `ls -lh docs/research/free-ai-tools-lifehacks.md`
Expected: File size is greater than 3KB.

---

### Task 2: Create English Free AI Tools & Lifehacks Guide

**Files:**
- Create: `docs/research/free-ai-tools-lifehacks_ENG.md`

**Step 1: Write the guide**
Translate and write the guide in English, matching all sections, links, warning boxes, and the Project Philosophy alignment exactly.

**Step 2: Run verification**
Verify the file exists and is not empty.
Run: `ls -lh docs/research/free-ai-tools-lifehacks_ENG.md`
Expected: File size is greater than 3KB.

---

### Task 3: Update Ukrainian README

**Files:**
- Modify: `README.md`

**Step 1: Update README.md**
- Insert the new file `docs/research/free-ai-tools-lifehacks.md` into the interactive repository tree.
- Add a new row to the "МОДУЛІ ТА НАВІГАЦІЯ" table.

**Step 2: Run verification**
Verify the changes are properly formatted.
Run: `git diff README.md`
Expected: Clean markdown diff with correct relative paths.

---

### Task 4: Update English README

**Files:**
- Modify: `README_ENG.md`

**Step 1: Update README_ENG.md**
- Mirror README.md updates in English, referencing `docs/research/free-ai-tools-lifehacks_ENG.md`.

**Step 2: Run verification**
Verify the changes are properly formatted.
Run: `git diff README_ENG.md`
Expected: Clean markdown diff with correct relative paths.

---

### Task 5: Final Verification & Commit (Signed & Verified)

**Files:**
- Modify: Git staging area

**Step 1: Setup Git Branch and Issue**
Create Git branch `feature/free-ai-tools-hacks`.

**Step 2: GPG Key Setup & Git Identity Setup**
Source Git Identity (`GITHUB_USER_NAME`, `GITHUB_USER_EMAIL`) from `/root/geminicli/.env` and import the GPG key `2D49E810C7F2527E` for signing commits.

**Step 3: Commit and Push**
Commit the changes using a signed commit, then delete the temporary private key to maintain security.
