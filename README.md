# claude-toolkit

A growing collection of workflows, automation scripts, and setup guides for running Claude and Claude Code in real-world environments.

Each subdirectory is a self-contained subproject with its own README and install instructions.

---

## Subprojects

| Subproject | Description |
|---|---|
| [`claude-code-remote`](./claude-code-remote) | Run Claude Code 24/7 on a VPS — accessible via Telegram, claude.ai, and the Claude mobile app |

---

## Adding a New Subproject

1. Create a new directory: `mkdir my-new-workflow`
2. Add a `README.md` explaining what it does, its requirements, and how to set it up
3. Add any scripts, configs, or supporting files
4. Update the table above

---

## Security Notes

- Never commit real API keys, bot tokens, or credentials
- Use `.env` files (covered by root `.gitignore`) or environment variables
- Each subproject's README has its own security checklist

---

## Contributing

Open an issue or PR to suggest a new workflow or improvement to an existing one.
