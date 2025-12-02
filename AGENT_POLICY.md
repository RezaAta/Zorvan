# Agent Mode Policy

This repository includes a formal policy for AI-assisted contributions ("agent mode"). The aim is to guide both human contributors and AI agents to preserve project quality, consistent commit patterns, and clear communication.

## Summary

- Preferred approach: advisory enforcement (CI reports violations but does not block merges at first).
- Agents must follow these rules where possible; maintainers can override in edge cases.

## Rules for Agents (short list)

1. Use test-driven development: Prefer first creating tests that reproduce the desired behavior, then implement the changes.
2. Keep commits small and contextual: Each commit should reflect a single logical change.
3. Use Conventional Commits (via Commitizen) for structure: `feat:`, `fix:`, `chore:`, `docs:`, `test:`.
4. Follow clean-code principles: Small functions, clear names, and readability (Uncle Bob principles).
5. Prefer short answers in PR descriptions, commit messages, and code comments; use a TL;DR when longer descriptions are necessary.
6. Add tests for any new behavior and update documentation accordingly.

## Agent-specific requirements

- When adding code: Ensure tests accompany the change and run successfully locally.
- When generating PRs: Include a short `TL;DR:` section at the top of PR descriptions.

## Operational Notes
- CI will run advisory checks on PRs; it will report failures but not block merging unless maintainers change branch protection rules.
- Over time, maintainers may make critical checks (like tests) blocking in CI.
