"""
Hermes agent client — Nous Research inference API (OpenAI-compatible).

Communication model:
  Me → inquiry → User → (approved) → Hermes → result → User → Me

Hermes handles tasks that require external research, API procurement,
or complex multi-step reasoning that benefits from a separate LLM pass.
All Hermes calls are initiated only after user approval.

API config (set in .env):
  NOUS_API_KEY   — Bearer token
  NOUS_PROJECT   — Project name (sent as metadata)
  NOUS_BASE_URL  — Inference base URL (default: https://inference.nousresearch.com/v1)
  NOUS_MODEL     — Model name (default: Hermes-3-Llama-3.1-70B)
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import requests

_KEY = os.environ.get("NOUS_API_KEY", "")
_PROJECT = os.environ.get("NOUS_PROJECT", "")
_BASE = os.environ.get("NOUS_BASE_URL", "https://inference.nousresearch.com/v1")
_MODEL = os.environ.get("NOUS_MODEL", "Hermes-3-Llama-3.1-70B")


@dataclass
class HermesTask:
    task_type: str          # see TASK_TYPES below
    prompt: str             # the specific question or instruction
    context: dict = field(default_factory=dict)  # optional structured context


@dataclass
class HermesResult:
    ok: bool
    content: str            # response text or error message
    task_type: str
    model: str = ""
    tokens_used: int = 0


# Defined task types — only these route to Hermes
TASK_TYPES = {
    "research":      "General market research and analysis",
    "api_guide":     "How to access a specific API or data source",
    "trade_review":  "Second opinion on a trade setup (non-binding)",
    "news_summary":  "Summarize and assess news impact on a symbol",
    "sector_scan":   "Identify momentum sectors or leading stocks",
    "risk_review":   "Review a proposed trade for risk/reward quality",
    "code_patch":    "Return a concrete code implementation given file context and a spec",
}

# System prompt override for code_patch tasks — optimized for implementation output
_CODE_PATCH_SYSTEM = (
    "You are Hermes, an expert Python implementer. "
    "Given file context and a specification, return ONLY the complete, ready-to-apply code. "
    "No explanations, no prose — just the implementation. "
    "If the spec is ambiguous, pick the most conservative interpretation that satisfies the requirement."
)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_KEY}",
        "Content-Type": "application/json",
        "X-Project": _PROJECT,
    }


def _chat(system: str, user: str, max_tokens: int = 512) -> dict | None:
    if not _KEY:
        return None
    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    try:
        r = requests.post(
            f"{_BASE}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"_error": str(e)}


def run_task(task: HermesTask) -> HermesResult:
    """
    Execute a pre-approved Hermes task.
    Caller is responsible for obtaining user approval before calling this.
    """
    if task.task_type not in TASK_TYPES:
        return HermesResult(
            ok=False,
            content=f"Unknown task type '{task.task_type}'. Valid: {', '.join(TASK_TYPES)}",
            task_type=task.task_type,
        )

    if not _KEY:
        return HermesResult(
            ok=False,
            content="NOUS_API_KEY not set — Hermes unavailable.",
            task_type=task.task_type,
        )

    system = _CODE_PATCH_SYSTEM if task.task_type == "code_patch" else (
        "You are Hermes, a financial research assistant supporting a momentum trading system. "
        "Be concise, factual, and structured. Never give financial advice that bypasses "
        "explicit risk rules. Always flag uncertainty."
    )

    max_tokens = 2048 if task.task_type == "code_patch" else 512

    context_block = ""
    if task.context:
        lines = "\n".join(f"  {k}: {v}" for k, v in task.context.items())
        context_block = f"\n\nContext:\n{lines}"

    user_msg = f"[{task.task_type.upper()}]\n{task.prompt}{context_block}"

    raw = _chat(system, user_msg, max_tokens=max_tokens)

    if raw is None or "_error" in raw:
        err = (raw or {}).get("_error", "No response")
        return HermesResult(ok=False, content=f"API error: {err}", task_type=task.task_type)

    try:
        content = raw["choices"][0]["message"]["content"].strip()
        model = raw.get("model", _MODEL)
        tokens = raw.get("usage", {}).get("total_tokens", 0)
        return HermesResult(ok=True, content=content, task_type=task.task_type, model=model, tokens_used=tokens)
    except (KeyError, IndexError) as e:
        return HermesResult(ok=False, content=f"Parse error: {e} — raw: {raw}", task_type=task.task_type)


def is_available() -> bool:
    """Quick connectivity check against the models endpoint."""
    if not _KEY:
        return False
    try:
        r = requests.get(f"{_BASE}/models", headers=_headers(), timeout=8)
        return r.status_code == 200
    except Exception:
        return False


def describe_tasks() -> str:
    """Return human-readable list of supported task types for user reference."""
    lines = ["Hermes task types:"]
    for t, desc in TASK_TYPES.items():
        lines.append(f"  {t:<14} — {desc}")
    return "\n".join(lines)
