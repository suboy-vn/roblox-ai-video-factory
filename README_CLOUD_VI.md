# ROBLOX AI VIDEO FACTORY 2.0 — CLOUD EDITION

Cloud Edition runs on Streamlit Community Cloud. It is isolated on the **cloud-edition** Git branch. The Windows Edition remains on **main** and its files are not changed by this Cloud branch.

## Deploy on Streamlit Community Cloud

Use these settings:

- Repository: `suboy-vn/roblox-ai-video-factory`
- Branch: `cloud-edition`
- Main file path: `app.py`

Do not deploy the `main` branch for this Cloud app; `main` is reserved for the Windows Edition.

## Streamlit Secrets

In Streamlit Community Cloud → app → Settings → Secrets, add TOML values:

```toml
APP_PASSWORD = "choose-a-long-unique-password"
OWNER_ID = "owner"
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_MODEL = "gpt-4.1-mini"

SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-supabase-service-role-key"
```

- `APP_PASSWORD` protects this single-owner MVP dashboard.
- `OPENAI_API_KEY` enables AI Story, Character AI, World Builder, Scene Director, Sound Studio and SEO Manager.
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` enable persistent database storage. If they are absent, app data is session-only and may disappear when the session restarts.
- Never commit secrets, tokens, Supabase service-role keys, or private user data to GitHub.

## Supabase database setup

1. Create a Supabase project.
2. Open SQL Editor.
3. Run the contents of `SUPABASE_SCHEMA.sql`.
4. Copy the project URL and service-role key into Streamlit Secrets.
5. Restart/reboot the Streamlit app.

The table stores JSON records for stories, characters, worlds, director plans, sound timelines, SEO packages, jobs, QC reports and batches. Row-level security is enabled; no public/anonymous policies are created. The privileged service-role key is used only by the server.

## Available Cloud modules

- Dashboard and project counters
- AI Story generation (JSON Story Bible)
- Character AI (Character Bible)
- World Builder (World Plan; descriptive plan, not a built Roblox place)
- Scene Director (Director Plan)
- Sound Studio (Sound Timeline; it does not synthesize or host audio)
- Thumbnail Studio (three text-layout variants from an uploaded image)
- SEO Manager (titles, descriptions, tags, hashtags and prompts)
- Production Manager (exports a Production Job JSON for a Windows Agent)
- Quality Control (schema/basic completeness checks)
- Batch Production (JSON queue)

## Windows-only tasks

Cloud Edition does not run Roblox Studio, OBS Studio, Windows executables, or local FFmpeg. It exports a Production Job JSON for the Windows Production Agent. The Agent's authenticated API, polling/acknowledgement protocol, artifact upload and status callbacks are **not implemented in this MVP**. Until that Agent exists, download the job JSON and move it to the Windows computer manually.

YouTube upload/OAuth is also not implemented in this Cloud MVP. SEO metadata can be exported for manual use.

## Security and current scope

- This is a single-owner password-gated MVP, not a multi-user SaaS authentication system.
- The app password is shared by all people who know it. Use a long unique password and keep the app URL private.
- The Supabase service-role key bypasses RLS; never expose it client-side or publish it.
- Streamlit session-only mode is temporary and not durable.
- Uploaded thumbnail images are processed in memory and download links are offered; no permanent image storage is configured in this MVP.
- No unattended publishing occurs.

## Local run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For local runs, create `.streamlit/secrets.toml` using the same TOML keys above. This file is ignored by Git.
