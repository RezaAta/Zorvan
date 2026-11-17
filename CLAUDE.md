@AGENTS.md

## Claude Code notes

- `.claude/settings.json` makes Claude Code ask before git writes (commit,
  push, branch creation, tag, merge, rebase, worktree). These prompts back up
  ground rule 1; don't try to work around them.
- Personal overrides go in `.claude/settings.local.json` or `CLAUDE.local.md`
  (both git-ignored).
- Prefer the dedicated file tools; use the scratchpad or system temp directory
  for throwaway scripts, never the repository.
