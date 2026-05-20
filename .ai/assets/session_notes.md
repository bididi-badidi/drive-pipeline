# Session Handover Notes

## 2026-05-20 — Skeleton scaffolded

All v1 skeleton files created. Every module has correct imports and function
signatures but no real logic yet — each is a working stub, not a TODO placeholder.

Next session should start with:
1. `uv sync` to install deps
2. Drop a test file into originals/ and run `python main.py` to verify the
   watcher + queue plumbing before touching processors.
3. Implement processors one at a time (document → image → url).

No unresolved design questions at this point — the PLAN.md is the source of truth.
