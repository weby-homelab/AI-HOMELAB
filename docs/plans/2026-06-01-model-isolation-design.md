# Plan: AI Model Isolation & Sandboxing Guide Integration

- **Date:** 2026-06-01
- **Status:** Approved
- **Scope:** Create a new guide (`projects/ai/docs/security/model_isolation.md`) outlining June 2026 model isolation best practices. Update `README.md` and `README_ENG.md` to reference it instead of `(coming soon)`.

## Threat Model (Updated)
- **Arbitrary Code Execution:** Escaping the sandbox / exploit kernel vulnerabilities (container escape).
- **Tool Abuse / Capability Escalation:** Exploiting legitimate tools to access secrets/data and exfiltrate it without kernel escapes.
- **Model & Intellectual Property Theft:** Theft of weights, LoRA adapters, embeddings, knowledge base, prompts, and system instructions.

## Isolation Levels & Recommended Stack
- **Firecracker:** MicroVMs for untrusted code execution, Python environments, and browser agents.
- **gVisor:** User-space syscall filtering for higher compatibility and lower overhead in K8s/Docker environments.
- **WASM:** Sandbox environment for deterministic tools, parsers, and lightweight functions.
- **Confidential Computing (TEE):** AMD SEV-SNP, Intel TDX, AWS Nitro Enclaves, and Nvidia Confidential GPUs for protecting data-in-use.
- **Zero-Trust Network:** TLS inspection, egress proxies, DNS exfiltration detection, and vsock communication.
