# claude-code-remote

[![CI](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/claude-code-remote-ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/claude-toolkit/actions/workflows/claude-code-remote-ci.yml)

Run Claude Code 24/7 on a cloud VPS — accessible via Telegram bot, Claude mobile app, and claude.ai — with no local machine required.

---

## Architecture

```
Telegram message
      ↓
  bot.py (VPS)  ──→  claude -p "task"  ──→  Anthropic API
      ↓                                           ↓
  reply back                              result returned

claude.ai / mobile  ──→  --remote flag  ──→  GitHub repo tasks (Anthropic cloud)
                    ──→  remote-control ──→  live VPS session stream
```

---

## Cost

| Item             | Cost           |
|------------------|----------------|
| Hetzner CX22 VPS | ~€4/month      |
| Claude Pro       | $20/month      |
| **Total**        | **~$25/month** |

---

## Quick Start

### Option A — Automated deploy via GitHub Actions (recommended)

1. Fork or push this repo to GitHub
2. Add the required secrets — see [`../.github/SECRETS.md`](../.github/SECRETS.md)
3. Go to **Actions → CI › claude-code-remote → Run workflow**, set `deploy=true`
4. GitHub Actions will SSH into your VPS, run `install.sh`, and start the bot — no manual steps

### Option B — Manual setup

```bash
git clone https://github.com/YOUR_USERNAME/claude-toolkit
cd claude-toolkit/claude-code-remote
chmod +x install.sh
./install.sh
```

Then edit `bot.py` and set your `BOT_TOKEN` and `ALLOWED_USER_ID` before starting the bot.

> **Security:** Never commit real tokens or API keys. Use environment variables or a `.env` file (already in `.gitignore`).

### Deploying a new version

```bash
# Tag a release — triggers CI, creates a GitHub Release, and auto-deploys to VPS
git tag claude-code-remote/v1.0.0
git push origin claude-code-remote/v1.0.0
```

---

## Phase 1 — Provision & Secure the VPS

**Provider:** Hetzner Cloud (hetzner.com)
**Specs:** CX22 — 2 vCPUs, 4GB RAM, 40GB SSD, Ubuntu 24.04 LTS

Claude Code is API-bound (inference runs on Anthropic's servers), so the VPS only needs to hold project files and run the Claude Code process — no GPU required.

```bash
# Create non-root user
adduser yourname && usermod -aG sudo yourname
su - yourname

# Disable root + password SSH login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no
sudo systemctl restart sshd

# Enable firewall
sudo ufw allow OpenSSH && sudo ufw enable
```

---

## Phase 2 — Install Node.js & Claude Code

```bash
# Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Claude Code
npm install -g @anthropic-ai/claude-code

# Authenticate (opens a URL to approve in any browser)
claude
```

Or authenticate with an API key:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

---

## Phase 3 — Persistent Sessions with tmux

```bash
sudo apt install tmux

cat > ~/.tmux.conf << 'EOF'
set -g mouse on
set -g default-terminal "screen-256color"
bind r source-file ~/.tmux.conf
EOF

# Create a persistent dev session
tmux new -s dev
# Detach: Ctrl+B then D
# Reattach: tmux attach -t dev
```

---

## Phase 4 — Claude Mobile + Web Access

### A) Cloud execution (`--remote`)

Connect your GitHub repo once from inside Claude Code:

```bash
/web-setup
```

Then kick off tasks from anywhere:

```bash
claude --remote "refactor the auth module"
```

Monitor and steer via **claude.ai** or the **Claude mobile app**. Sessions persist even when your laptop is closed. Requires a GitHub-hosted repo.

### B) VPS execution (`remote-control`)

```bash
claude remote-control
```

Gives you a streaming link you can open in any browser or the Claude mobile app. Your phone becomes a live window into the VPS session — full filesystem, MCP servers, and tools intact.

> **Key difference:** `--remote` runs tasks in Anthropic's cloud. `remote-control` keeps execution on your VPS and routes the UI through Anthropic's relay.

---

## Phase 5 — Telegram Bot

Send tasks to Claude Code from anywhere, get results back in chat.

### Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) → copy your `BOT_TOKEN`
2. Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
3. Set `BOT_TOKEN` and `ALLOWED_USER_ID` in `bot.py`
4. Run in a persistent tmux session:

```bash
tmux new -s tgbot
python3 ~/claude-code-remote/bot.py
# Ctrl+B D to detach
```

### Bot Commands

| Command   | Action                                       |
|-----------|----------------------------------------------|
| Any text  | Runs `claude -p "<your message>"` on the VPS |
| `/cancel` | Kills the currently running task             |
| `/status` | Shows task state, prompt preview, elapsed time |

### Features

- Rate limit detection with automatic retry (10s → 30s → 60s backoff)
- 3-minute task timeout with friendly message
- Live status updates edited in-place (no message spam)
- Busy guard — blocks new tasks while one is running
- Restricted to your Telegram user ID only

---

## Phase 6 — Auto-start on Reboot

```bash
crontab -e

# Add:
@reboot tmux new-session -d -s dev
@reboot sleep 5 && cd ~/claude-code-remote && tmux new-session -d -s tgbot 'python3 bot.py'
```

---

## Parallel Usage

| Combination                       | Works? | Notes                                       |
|-----------------------------------|--------|---------------------------------------------|
| Telegram bot + `--remote`         | ✅ Yes  | Fully independent — different executors     |
| Telegram bot + Remote Control     | ⚠️ Yes | Share VPS resources and account rate limits |
| `--remote` + Remote Control open  | ✅ Yes  | Separate sessions, different tasks          |
| Two Telegram tasks simultaneously | ❌ No   | Bot blocks second task until first is done  |

For heavy parallel workloads, consider upgrading to **Claude Max** ($100/month) for higher rate limits.

---

## Security Checklist

- [ ] Root login disabled
- [ ] Password SSH login disabled
- [ ] Non-root user with sudo
- [ ] UFW firewall enabled (SSH only)
- [ ] Bot restricted to your Telegram user ID only
- [ ] API key in `~/.bashrc` or `.env`, never hardcoded
- [ ] tmux sessions named and documented

---

## Daily Commands

```bash
# Reattach to dev session
tmux attach -t dev

# Check bot is running
tmux attach -t tgbot

# Run a one-off task headlessly
claude -p "your task here"

# Start a remote task (monitored via mobile)
claude --remote "your task here"

# List tmux sessions
tmux ls
```
