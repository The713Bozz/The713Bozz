---
name: ponytail-review
description: >
  Over-engineering review of a diff or code block. Hunts for what can be
  deleted: reinvented stdlib, unneeded dependencies, speculative abstractions,
  dead flexibility. Returns one-line findings tagged delete/stdlib/native/yagni/shrink
  with a net line count. Use when the user says "ponytail-review", "/ponytail-review",
  "review for bloat", "check for over-engineering", or "is this too complex".
  One-shot, does not apply fixes.
license: MIT
---

# Ponytail Review

Hunt exclusively for complexity. Correctness bugs, security holes, and
performance go to a normal review pass — not here.

## Tags

- `delete:` unused code, dead feature, speculative flexibility. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library already ships. Name the built-in.
- `native:` dependency or wrapper duplicating a platform feature. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller. Inline until a second use appears.
- `shrink:` same logic, fewer lines. Show the condensed form inline.

## Output Format

One line per finding:

`L<line>: <tag> <what>. <replacement>.`

End with: `net: -<N> lines possible.`
Nothing to cut: `Lean already. Ship.`

## Scope

Complexity only. A single smoke test or `assert`-based self-check is not
bloat — leave it. The goal is deletion, not correctness.

One-shot. "stop ponytail-review" or "normal mode" to revert.
