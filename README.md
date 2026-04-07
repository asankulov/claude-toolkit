# claude-toolkit

[![CI Dispatcher](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/ci-dispatch.yml/badge.svg)](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/ci-dispatch.yml)
[![Release](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/release.yml/badge.svg)](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/release.yml)
[![Dependency Check](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/dependency-check.yml/badge.svg)](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/dependency-check.yml)

A growing collection of workflows, automation scripts, and setup guides for running Claude and Claude Code in real-world environments.

Each subdirectory is a self-contained subproject with its own README, CI pipeline, and one-command deploy.

---

## Subprojects

| Subproject | Description | CI |
|---|---|---|
| [`claude-code-remote`](./claude-code-remote) | Run Claude Code 24/7 on a VPS — accessible via Telegram, claude.ai, and the Claude mobile app | [![CI](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/claude-code-remote-ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/claude-code-remote-ci.yml) |

---

## CI/CD Architecture

```
push to main
      │
      ▼
ci-dispatch.yml          ← detects which subproject changed
      │
      ├── claude-code-remote changed?
      │         └── claude-code-remote-ci.yml
      │                   ├── lint (flake8 + shellcheck)
      │                   ├── secret scan (gitleaks)
      │                   └── deploy to VPS  ← manual trigger or tag push
      │
      └── (future subprojects auto-wired here)

push tag claude-code-remote/vX.Y.Z
      └── release.yml → GitHub Release + auto-deploy

schedule (Monday 09:00 UTC)
      └── dependency-check.yml → opens issue if packages are outdated
```

See [`.github/SECRETS.md`](.github/SECRETS.md) for the list of secrets to configure before using the deploy job.

---

## Adding a New Subproject

1. Create a new directory: `mkdir my-new-workflow`
2. Add a `README.md` explaining what it does, its requirements, and how to set it up
3. Add any scripts, configs, or supporting files
4. Add a path filter entry for it in `.github/workflows/ci-dispatch.yml`
5. Create `.github/workflows/my-new-workflow-ci.yml` following the same pattern as `claude-code-remote-ci.yml`
6. Update the subprojects table above

---

## Security Notes

- Never commit real API keys, bot tokens, or credentials
- Use `.env` files (covered by root `.gitignore`) or environment variables
- Each subproject's README has its own security checklist

---

## Contributing

Open an issue or PR to suggest a new workflow or improvement to an existing one.
