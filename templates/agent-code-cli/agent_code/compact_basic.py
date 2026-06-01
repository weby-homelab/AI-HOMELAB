from __future__ import annotations

from typing import Any


def compact(messages: list[dict[str, Any]], keep: int = 8) -> list[dict[str, Any]]:
    pin_count = 2
    if len(messages) <= keep + pin_count:
        return messages

    pinned = messages[:pin_count]
    working = messages[-keep:]
    middle = messages[pin_count:-keep]
    compressed = _build_compressed_block(middle)
    return pinned + [compressed] + working


def _build_compressed_block(msgs: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(msgs)
    tool_names: set[str] = set()
    tool_count = 0
    files_read: set[str] = set()
    files_edited: set[str] = set()
    commands: list[str] = []
    previous_summary: str | None = None

    for msg in msgs:
        content = msg.get("content")
        if isinstance(content, str) and content.startswith("<compacted-history>"):
            previous_summary = content
            continue
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype == "tool_use":
                tool_count += 1
                name = block.get("name", "")
                if name:
                    tool_names.add(name)
                args = block.get("input", {}) or {}
                if name in ("read_file",) and args.get("path"):
                    files_read.add(str(args["path"]))
                elif name in ("file_write", "file_edit") and args.get("file_path"):
                    files_edited.add(str(args["file_path"]))
                elif name == "bash" and args.get("command"):
                    cmd = str(args["command"])
                    commands.append(cmd[:80] + "..." if len(cmd) > 80 else cmd)

    lines = ["<compacted-history>"]
    if previous_summary:
        lines.append("  <previous-summary>")
        for ln in previous_summary.splitlines():
            lines.append("    " + ln)
        lines.append("  </previous-summary>")
    lines.extend(
        [
            f"  <message-count>{total}</message-count>",
            f"  <tool-calls>{tool_count}</tool-calls>",
            f"  <tools-used>{', '.join(sorted(tool_names)) if tool_names else '(none)'}</tools-used>",
            f"  <files-read>{', '.join(sorted(files_read)) if files_read else '(none)'}</files-read>",
            f"  <files-edited>{', '.join(sorted(files_edited)) if files_edited else '(none)'}</files-edited>",
            f"  <commands-run>{', '.join(commands[:20]) if commands else '(none)'}</commands-run>",
            "</compacted-history>",
        ]
    )
    return {"role": "user", "content": "\n".join(lines)}
