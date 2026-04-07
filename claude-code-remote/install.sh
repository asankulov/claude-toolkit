#!/bin/bash
# install.sh — Claude Code Remote Setup
# Tested on Ubuntu 24.04 LTS (Hetzner CX22)
# Run as a non-root user with sudo access.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[+]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[x]${NC} $1"; exit 1; }
ask()     { echo -e "${YELLOW}[?]${NC} $1"; }

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] && error "Do not run as root. Create a non-root user first."

info "Starting Claude Code Remote setup..."

# ── System update ─────────────────────────────────────────────────────────────
info "Updating system packages..."
sudo apt-get update -qq && sudo apt-get upgrade -y -qq

# ── Essential tools ───────────────────────────────────────────────────────────
info "Installing tmux, ripgrep, git, python3-pip..."
sudo apt-get install -y -qq tmux ripgrep git python3-pip curl

# ── Node.js 22 LTS ────────────────────────────────────────────────────────────
info "Installing Node.js 22 LTS..."
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - > /dev/null 2>&1
sudo apt-get install -y -qq nodejs

node_version=$(node --version)
info "Node.js installed: $node_version"

# ── Claude Code ───────────────────────────────────────────────────────────────
info "Installing Claude Code..."
npm install -g @anthropic-ai/claude-code > /dev/null 2>&1

claude_version=$(claude --version 2>/dev/null || echo "unknown")
info "Claude Code installed: $claude_version"

# ── Auth ──────────────────────────────────────────────────────────────────────
echo ""
warn "Authentication: choose one option:"
echo "  1) Claude Pro/Max account (OAuth — opens a browser URL)"
echo "  2) Anthropic API key"
echo ""
ask "Enter your ANTHROPIC_API_KEY (or press Enter to use OAuth):"
read -r API_KEY

if [[ -n "$API_KEY" ]]; then
    echo "export ANTHROPIC_API_KEY=\"$API_KEY\"" >> ~/.bashrc
    export ANTHROPIC_API_KEY="$API_KEY"
    info "API key saved to ~/.bashrc"
else
    warn "Run 'claude' after this script to complete OAuth authentication."
fi

# ── tmux config ───────────────────────────────────────────────────────────────
info "Writing ~/.tmux.conf..."
cat > ~/.tmux.conf << 'EOF'
set -g mouse on
set -g default-terminal "screen-256color"
set -g history-limit 10000
bind r source-file ~/.tmux.conf \; display "Config reloaded"
EOF

# ── Telegram bot ──────────────────────────────────────────────────────────────
info "Installing python-telegram-bot..."
pip3 install python-telegram-bot --break-system-packages -q

BOT_DIR="$HOME/claude-code-remote"
mkdir -p "$BOT_DIR"

if [[ ! -f "$BOT_DIR/bot.py" ]]; then
    warn "bot.py not found at $BOT_DIR/bot.py"
    warn "Copy bot.py from this repo and set BOT_TOKEN + ALLOWED_USER_ID before starting."
else
    info "bot.py found at $BOT_DIR/bot.py"
    warn "Make sure BOT_TOKEN and ALLOWED_USER_ID are set in bot.py before starting the bot."
fi

# ── Crontab (auto-start on reboot) ────────────────────────────────────────────
info "Configuring crontab for auto-start on reboot..."

CRON_DEV="@reboot tmux new-session -d -s dev"
CRON_BOT="@reboot sleep 5 && cd $BOT_DIR && tmux new-session -d -s tgbot 'set -a && source $BOT_DIR/.env && set +a && python3 $BOT_DIR/bot.py'"

( crontab -l 2>/dev/null | grep -v "tmux new-session"; echo "$CRON_DEV"; echo "$CRON_BOT" ) | crontab -

info "Crontab updated."

# ── UFW firewall ──────────────────────────────────────────────────────────────
info "Configuring UFW firewall (SSH only)..."
sudo ufw --force reset > /dev/null 2>&1
sudo ufw allow OpenSSH > /dev/null 2>&1
sudo ufw --force enable > /dev/null 2>&1
info "UFW enabled — only SSH allowed inbound."

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit bot.py and set BOT_TOKEN + ALLOWED_USER_ID"
echo "     nano $BOT_DIR/bot.py"
echo ""
if [[ -z "$API_KEY" ]]; then
echo "  2. Authenticate with Claude:"
echo "     claude"
echo ""
echo "  3. Start the Telegram bot:"
else
echo "  2. Start the Telegram bot:"
fi
echo "     source ~/.bashrc"
echo "     tmux new -s tgbot"
echo "     python3 $BOT_DIR/bot.py"
echo "     (Ctrl+B D to detach)"
echo ""
echo "  For GitHub/web sessions: run /web-setup inside Claude Code"
echo ""
echo "  See PLAN.md for full reference."
echo ""
