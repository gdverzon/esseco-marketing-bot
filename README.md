# ESSECO AI Marketing Employee System

Codex Bot is a local-first AI Marketing Employee System built with Python, Streamlit, SQLite, and the OpenAI Codex CLI. Phase 1 provides a configurable marketing knowledge base, specialized content generators, a saved-content library, exports, and a human-review lifecycle.

Configured business: **Esse Co Handcrafted Essentials**, a Philippines-based online retailer of handcrafted essentials and personal-care products. Known product groups are massage oils and sprayer products; all unspecified details remain explicitly unverified.

## Features

- Dark-mode Streamlit dashboard and chat history
- Codex integration through `codex exec --json --sandbox read-only`
- Dedicated Facebook caption, product description, hashtag, and seven-day calendar generators
- Editable business, product, target-audience, and brand-voice knowledge base
- Saved marketing-content library with draft and approval status
- SQLite conversations and durable approval audit trail
- CSV and Markdown exports for conversations and saved marketing assets
- Rotating local activity logs with friendly UI errors
- Windows Task Scheduler registration only after a separate approval click
- No n8n, hosted database, or paid third-party integration
- No automatic publishing or external social-media connector
- AI Marketing Manager with automatic routing across 15 specialized capabilities
- Facebook, Instagram, TikTok/Reels, Shopee, and Lazada support
- Seven-day and 30-day Asia/Manila marketing calendars
- Campaign planning, customer-response suggestions, image prompts, quality review, and market-research planning
- Real stored-data overview and manually entered marketing analytics

## Phase 1 workflow

1. Open **Knowledge base** and replace the starter business, audience, brand-voice, and product information with verified facts.
2. Open **Content studio**, select a specialist generator, and provide a brief.
3. Codex runs in the existing read-only sandbox, returns validated structured JSON, and the manager sends it to `pending_approval`.
4. Open **Content library** to inspect the draft and submit it for approval.
5. A human marks pending content `approved` or `rejected`.
6. Export reviewed content as CSV or Markdown and publish it manually outside Codex Bot.

Approval records readiness only. The application never posts, uploads, emails, or purchases advertising.

### Content lifecycle

```text
draft → pending_approval → approved → scheduled → published (owner confirmation required)
                         ↘ rejected → draft
```

An approved record is final in Phase 1. Generate a new revision when further changes are needed.

## Configure the marketing knowledge base

The dashboard safely edits these local files:

- `knowledge/business.md`
- `knowledge/products.json`
- `knowledge/target_audience.md`
- `knowledge/brand_voice.md`
- `knowledge/marketing_goals.md`
- `knowledge/platform_guidelines.md`
- `knowledge/faq.md`

`knowledge/marketing_rules.md` remains a project-controlled safety policy. Product JSON is validated before an atomic save, and Markdown sections are size-limited. Do not store passwords, API keys, private customer records, payment information, or regulated data in any knowledge file.

## Marketing features

- **Overview:** actual counts from SQLite; no synthetic metrics.
- **AI marketing:** automatic or explicit skill routing with structured validation.
- **Calendar:** seven-day and 30-day generation, stored dated entries, platform filtering, Asia/Manila defaults.
- **SEO & listings:** SEO suggestions and factual Shopee/Lazada listing drafts.
- **Campaigns:** saved campaign plans.
- **Products:** local verified product management with unknown values left blank.
- **Approval queue:** edit, regenerate, approve, or reject content.
- **Content history:** filter content, export CSV/JSON/Markdown, mark scheduled, and explicitly confirm actual publication.
- **Analytics:** manually store real observed metrics; Phase 1 does not fetch platform analytics.
- **Chat, Skills lab, Scheduler:** original Codex Bot functionality remains available.

The manager supports content writing, Facebook captions, Instagram captions, TikTok/Reels scripts, hashtags, SEO keywords, Shopee listings, Lazada listings, campaigns, calendars, customer replies, image prompts, research planning, data analysis, and quality review.

Example product entry:

```json
{
  "products": [
    {
      "name": "Product name",
      "category": "Category",
      "description": "Verified factual description",
      "features": ["Verified feature"],
      "price": null,
      "url": null
    }
  ]
}
```

## Requirements

- Windows 10 or 11
- Python 3.10 or newer (64-bit recommended)
- OpenAI Codex CLI installed and authenticated
- 8 GB RAM is sufficient; the app uses lightweight local storage and runs one Codex process at a time

Codex access follows the authentication and plan available to your installed CLI. The app itself does not require another service or API key.

## Installation

Open PowerShell in this folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
codex.cmd login
.\run.ps1
```

Then open the local URL printed by Streamlit, normally `http://localhost:8501`.

Manual installation is also supported:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
codex login
python -m streamlit run app.py
```

## How scheduling works

The Scheduler page validates and stages a `schtasks.exe` command in SQLite. Nothing changes in Windows until you inspect the exact command and click **Approve and register**. Scheduled results are written to `outputs/`; failures go to `logs/activity.log`. Creating a task may require starting Streamlit from a PowerShell window with sufficient Windows permissions.

Scheduled generation is local automation, but Codex CLI still needs its normal authenticated network access when the task runs. Windows must be awake and the user context must be able to run the CLI.

## Privacy and safety

- Content requests run with Codex's `read-only` sandbox. The CLI repository check is skipped so the app also works from a normal non-Git folder; this does not broaden filesystem permissions.
- The process uses argument arrays and `shell=False`; user text is never interpolated into a shell command.
- Conversations, generated marketing assets, approval decisions, exports, and logs remain in this project by default.
- Codex Bot drafts external content but does not post, email, upload, or publish it.
- Back up `database/codex_bot.db` if conversation history matters to you.

## Project layout

```text
main.py                Windows-friendly application launcher
app.py                 Streamlit dashboard
AGENTS.md              Contributor and safety instructions
knowledge/             Editable business, product, audience, voice, and policy context
skills/                Content, SEO, campaign, research, and analytics specialists
workflows/             Reusable knowledge-to-Codex orchestration
codex_bot/             Core database, runner, prompts, exports, and scheduler modules
scheduled_job.py       Task Scheduler entry point
tests/                 Offline unit and UI tests
database/              Runtime SQLite database (ignored)
outputs/               Generated scheduled output (ignored)
logs/                  Rotating activity log (ignored)
```

SQLite migrations are additive and recorded in `schema_migrations`. The normalized Phase 1 model includes business profiles, products, tasks, generated content, campaigns, calendars and entries, approval history, metrics, and activity logs. Existing conversations, messages, legacy content, and scheduler approvals are preserved.

Edit the files in `knowledge/` to describe your real business. Codex Bot loads only the five allow-listed files and caps their combined prompt size. Do not place credentials or private customer data in these files. The **Skills lab** page combines that approved context with the focused modules in `skills/`.

The Phase 1 generators live in `skills/facebook_caption.py`, `skills/product_description.py`, `skills/hashtag_generator.py`, and `skills/content_calendar.py`. `codex_bot/marketing_service.py` loads approved knowledge, invokes the existing Codex runner, and persists successful results. The SQLite schema update is additive, so existing conversations and scheduler approvals are preserved.

On first startup after upgrading, an existing `data/codex_bot.db` is copied to `database/codex_bot.db` when the new database does not already exist. The legacy file is left untouched as a backup.

## Testing

The test suite is offline: it mocks Codex and never creates a Windows task.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall main.py app.py codex_bot skills workflows scheduled_job.py
```

To verify the CLI separately:

```powershell
codex --version
codex exec --sandbox read-only "Reply with: Codex is ready"
```

Structured marketing tasks use `codex exec --output-schema` and are validated again locally. If validation fails, the manager makes at most one correction attempt. This follows the [official OpenAI Codex structured workflow example](https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex).

## Troubleshooting

- **Codex CLI not found:** confirm `codex --version` works in the same PowerShell window, then restart Streamlit.
- **Authentication error:** run `codex login` interactively.
- **Task registration fails:** review the Activity page and `logs/activity.log`; Windows policy may require elevated Task Scheduler permissions.
- **A scheduled task runs but produces no file:** make sure Windows is awake, Codex remains authenticated, and the configured Python environment still exists.

The Codex JSONL automation and restricted-sandbox pattern follows the [official OpenAI Codex guidance](https://developers.openai.com/blog/eval-skills).

