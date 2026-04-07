import subprocess
import asyncio
import time
import os
import sys
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_user_id = os.environ.get("TELEGRAM_USER_ID", "")

if not BOT_TOKEN or not _user_id:
    sys.exit("❌ TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID must be set in the environment.")

try:
    ALLOWED_USER_ID = int(_user_id)
except ValueError:
    sys.exit("❌ TELEGRAM_USER_ID must be a numeric Telegram user ID.")

MAX_RETRIES = 3
RETRY_DELAYS = [10, 30, 60]        # Seconds between retries on rate limit
TASK_TIMEOUT = 180                 # Seconds before a task is killed

# ── State ─────────────────────────────────────────────────────────────────────
active_tasks: dict[int, asyncio.Task] = {}
active_processes: dict[int, subprocess.Popen] = {}
task_meta: dict[int, dict] = {}


# ── Exceptions ────────────────────────────────────────────────────────────────
class RateLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


class CancelledByUser(Exception):
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────
def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}m {secs}s"


def run_claude_sync(task: str, user_id: int) -> tuple[bool, str]:
    """Run claude -p synchronously, tracking the process for cancellation."""
    for attempt in range(1, MAX_RETRIES + 1):
        proc = subprocess.Popen(
            ["claude", "-p", task],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        active_processes[user_id] = proc

        if user_id in task_meta:
            task_meta[user_id]["attempt"] = attempt

        try:
            stdout, stderr = proc.communicate(timeout=TASK_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            active_processes.pop(user_id, None)
            raise TimeoutError()

        active_processes.pop(user_id, None)

        # Killed by /cancel (SIGKILL → returncode -9)
        if proc.returncode == -9:
            raise CancelledByUser()

        output = stdout.strip()
        error = stderr.strip()

        if proc.returncode == 0 and output:
            return True, output

        is_rate_limited = any(phrase in error.lower() for phrase in [
            "rate limit", "too many requests", "429", "overloaded"
        ])

        if is_rate_limited:
            raise RateLimitError(RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)])

        return False, error or "No output returned."

    return False, "Max retries exceeded."


# ── Handlers ──────────────────────────────────────────────────────────────────
async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle an incoming task message."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        return

    # Block if already busy
    if user_id in active_tasks and not active_tasks[user_id].done():
        await update.message.reply_text(
            "⚠️ A task is already running.\n"
            "Use /status to check it or /cancel to stop it."
        )
        return

    prompt = update.message.text
    status_msg = await update.message.reply_text("⏳ Working on it...")

    task_meta[user_id] = {
        "prompt": prompt,
        "started_at": time.time(),
        "attempt": 1,
        "state": "running",
    }

    async def run():
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                success, output = await asyncio.to_thread(
                    run_claude_sync, prompt, user_id
                )
                task_meta[user_id]["state"] = "done" if success else "failed"
                icon = "✅" if success else "❌"
                label = "Done" if success else "Error"
                await status_msg.edit_text(f"{icon} {label}:\n\n{output[:4000]}")
                return

            except CancelledByUser:
                task_meta[user_id]["state"] = "cancelled"
                await status_msg.edit_text("🛑 Task cancelled.")
                return

            except asyncio.CancelledError:
                proc = active_processes.pop(user_id, None)
                if proc:
                    proc.kill()
                task_meta[user_id]["state"] = "cancelled"
                await status_msg.edit_text("🛑 Task cancelled.")
                return

            except RateLimitError:
                if attempt < MAX_RETRIES:
                    wait = RETRY_DELAYS[attempt - 1]
                    task_meta[user_id]["state"] = "retrying"
                    await status_msg.edit_text(
                        f"⏸️ Rate limited. Retrying in {wait}s... "
                        f"({attempt}/{MAX_RETRIES})"
                    )
                    await asyncio.sleep(wait)
                    task_meta[user_id]["state"] = "running"
                else:
                    task_meta[user_id]["state"] = "failed"
                    await status_msg.edit_text(
                        "🚫 Rate limit hit — max retries reached.\n"
                        "Wait a few minutes and try again."
                    )
                    return

            except TimeoutError:
                task_meta[user_id]["state"] = "timed_out"
                await status_msg.edit_text(
                    f"⏱️ Task timed out after {TASK_TIMEOUT // 60} minutes.\n"
                    "Try breaking it into smaller steps."
                )
                return

            except Exception as e:
                task_meta[user_id]["state"] = "failed"
                await status_msg.edit_text(f"💥 Unexpected error:\n\n{str(e)[:500]}")
                return

    task_obj = asyncio.create_task(run())
    active_tasks[user_id] = task_obj


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/cancel — kill the currently running task."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        return

    task = active_tasks.get(user_id)
    if not task or task.done():
        await update.message.reply_text("ℹ️ No task is currently running.")
        return

    task.cancel()
    await update.message.reply_text("🛑 Cancelling...")


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/status — show what's running and how long it's been going."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        return

    meta = task_meta.get(user_id)
    task = active_tasks.get(user_id)

    if not meta:
        await update.message.reply_text("ℹ️ No tasks run yet this session.")
        return

    elapsed = format_duration(time.time() - meta["started_at"])
    prompt_preview = meta["prompt"][:80] + ("…" if len(meta["prompt"]) > 80 else "")
    attempt = meta.get("attempt", 1)
    state = meta.get("state", "unknown")
    is_active = task and not task.done()

    state_labels = {
        "running":   "⚙️ Running",
        "retrying":  "⏸️ Retrying (rate limited)",
        "done":      "✅ Completed",
        "cancelled": "🛑 Cancelled",
        "failed":    "❌ Failed",
        "timed_out": "⏱️ Timed out",
    }
    state_label = state_labels.get(state, f"❓ {state}")

    lines = [
        "📋 *Last task*",
        f"*Prompt:* `{prompt_preview}`",
        f"*Status:* {state_label}",
        f"*Elapsed:* {elapsed}",
    ]
    if is_active and attempt > 1:
        lines.append(f"*Attempt:* {attempt}/{MAX_RETRIES}")
    if is_active:
        lines.append("\nSend /cancel to stop it.")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Main ──────────────────────────────────────────────────────────────────────
async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("status", "Show current task state and elapsed time"),
        BotCommand("cancel", "Kill the currently running task"),
    ])


app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(CommandHandler("status", status))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot is running. Press Ctrl+C to stop.")
app.run_polling()
