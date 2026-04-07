#!/bin/bash
# push-to-github.sh
# Run this once from your local machine to create the GitHub repo and push.
# Requirements: gh CLI installed and authenticated (gh auth login)

set -e

REPO_NAME="claude-toolkit"
VISIBILITY="public"   # change to "private" if preferred

echo "[+] Creating GitHub repo: $REPO_NAME ($VISIBILITY)..."
gh repo create "$REPO_NAME" --"$VISIBILITY" --description "A collection of Claude Code workflows, automations, and setup guides" --source=. --remote=origin --push

echo ""
echo "[✓] Done! Your repo is live at: https://github.com/$(gh api user --jq .login)/$REPO_NAME"
