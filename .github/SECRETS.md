# GitHub Actions — Required Secrets

Go to **Settings → Secrets and variables → Actions** in your repo and add these.

## Root repo secrets (used by all workflows)

| Secret | Description |
|---|---|
| *(none required at root level)* | Root workflows delegate to subprojects |

---

## claude-code-remote secrets

Required only if you use the **Deploy to VPS** job.

| Secret | Description | Example |
|---|---|---|
| `VPS_HOST` | IP address or hostname of your VPS | `123.456.78.9` |
| `VPS_USER` | SSH username (non-root) | `yourname` |
| `VPS_SSH_KEY` | Private SSH key for the VPS user | Contents of `~/.ssh/id_ed25519` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (used by install.sh on first boot) | `sk-ant-...` |

### How to generate an SSH key pair for CI

```bash
# On your local machine — generate a dedicated CI key (no passphrase)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/claude_toolkit_deploy -N ""

# Copy the public key to your VPS
ssh-copy-id -i ~/.ssh/claude_toolkit_deploy.pub yourname@YOUR_VPS_IP

# Add the private key to GitHub secrets as VPS_SSH_KEY
cat ~/.ssh/claude_toolkit_deploy
```

### GitHub Environment (production gate)

The deploy job uses a GitHub **Environment** named `production` so you can require manual approval before any deployment runs.

To set it up: **Settings → Environments → New environment → name it `production`** → enable "Required reviewers" and add yourself.

---

## Triggering a deploy manually

Once secrets are configured:

1. Go to **Actions → CI › claude-code-remote (stub) → Run workflow**
2. Set `deploy` to `true`
3. Click **Run workflow**

Or push a tag to auto-deploy and create a release:

```bash
git tag claude-code-remote/v1.0.0
git push origin claude-code-remote/v1.0.0
```

---

## Workflow file convention

GitHub Actions requires `workflow_call` files to live under the root `.github/workflows/`.
This repo uses a two-file pattern per subproject:

```
.github/workflows/<subproject>.yml        ← thin root stub (required by GitHub)
<subproject>/.github/workflows/ci.yml     ← full pipeline logic (lives with the code)
```

The stub is auto-generated boilerplate. Always edit the subproject's own `ci.yml`.
