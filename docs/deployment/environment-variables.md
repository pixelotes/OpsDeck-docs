# Environment Variables

OpsDeck is configured entirely via environment variables. Set them in your OS, in your container orchestrator, or in a `.env` file in the project root. The `.env` file is read by the `flask` command (through python-dotenv) and by Docker Compose (`env_file: .env`); gunicorn does not read it on its own. `.env.example` in the repository lists the common settings with comments.

## General

| Variable | Description | Default | Required |
|---|---|---|---|
| `SECRET_KEY` | Cryptographic signing key for sessions and CSRF. Also used to derive the encryption key for stored secrets when `DATA_ENCRYPTION_KEY` is unset. Must be long and random. | `your-secret-key-change-this` | **Yes** |
| `DATA_ENCRYPTION_KEY` | Fernet key(s) that encrypt stored secrets such as API connector credentials. Separate several keys with commas: the first encrypts and all of them decrypt. See [Security Hardening](security-hardening.md#encryption-of-stored-secrets). | Derived from `SECRET_KEY` | Recommended |
| `APP_BASE_URL` | Public URL of OpsDeck, such as `https://opsdeck.example.com`. Used to build absolute links in emails sent by background jobs, such as supplier review notifications. | `''` | Recommended |
| `TIMEZONE` | Application timezone, as an IANA name such as `Europe/Madrid`, `America/New_York` or `UTC`. Used for dates shown in the UI and for the times of scheduled jobs. An unknown name falls back to `Europe/Madrid`. | `Europe/Madrid` | No |
| `FLASK_APP` | Tells the `flask` command where the application is. The Docker image and the Helm chart set it; set it yourself only for a manual installation. | `run:app` in the image | Manual installs only |
| `FLASK_DEBUG` | Enable debug mode. `1` for development, `0` for production. | `0` | No |
| `FLASK_ENV` | When set to `development`, HTTPS redirection is turned off. The Helm chart sets it to `production`. | — | No |

## Database

| Variable | Description | Default | Required |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URI. Format: `postgresql://user:pass@host:port/dbname`. A Heroku-style `postgres://` prefix is rewritten to `postgresql://`. | — | **Yes** |

## Web server and proxy

| Variable | Description | Default |
|---|---|---|
| `TRUST_PROXY` | Set to `1` (or `true`, `yes`, `on`) when OpsDeck runs behind a reverse proxy or ingress. The app then honours the `X-Forwarded-For`, `-Proto`, `-Host` and `-Prefix` headers, so absolute URLs such as OAuth redirect URIs and email links use the public host and `https`. Leave it unset when clients connect directly. | unset |
| `GUNICORN_WORKERS` | Number of gunicorn worker processes started by the container entrypoint. | `2` |
| `GUNICORN_THREADS` | Threads per gunicorn worker. | `4` |

## Uploads

| Variable | Description | Default |
|---|---|---|
| `MAX_UPLOAD_MB` | Maximum size of any request body, in megabytes. It applies to every request, so it caps attachments, imports and form posts alike. Larger requests are rejected with a "file is too large" message (HTTP 413). Minimum `1`. | `5` |
| `UPLOAD_ALLOWED_EXTENSIONS` | Comma-separated list of file extensions accepted by every upload in the app, such as `jpg,png,pdf,docx,csv,zip`. Setting it replaces the built-in list. | Built-in list, see below |

The built-in list covers images and scans (`jpg`, `jpeg`, `png`, `gif`, `bmp`, `tga`, `webp`, `tif`, `tiff`, `heic`, `heif`), documents (`pdf`, `odt`, `ods`, `odp`, `doc`, `docx`, `xls`, `xlsx`, `ppt`, `pptx`, `rtf`, `txt`, `md`), data (`csv`, `tsv`, `json`, `xml`, `log`), archives (`zip`, `7z`, `gz`, `tar`, `tgz`, `rar`), saved email (`eml`, `msg`) and certificates (`pem`, `crt`, `cer`, `der`). `svg`, `html`, `htm` and executables are left out on purpose because they can carry script; adding them back re-opens that risk.

## Admin initialization

These are used only on the first run to create the initial admin user.

| Variable | Description | Default |
|---|---|---|
| `DEFAULT_ADMIN_EMAIL` | Admin user email. | `admin@example.com` |
| `DEFAULT_ADMIN_INITIAL_PASSWORD` | Admin user initial password. Changed on first login. | `admin123` |

## Email / SMTP

| Variable | Description | Default |
|---|---|---|
| `SMTP_SERVER` | SMTP server hostname. | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port. | `587` |
| `EMAIL_USERNAME` | SMTP authentication username. Also used as the sender address. | `''` |
| `EMAIL_PASSWORD` | SMTP authentication password or app password. | `''` |
| `EMAIL_SENDER_NAME` | Display name in the `From` header, such as `OpsDeck`. When empty, the `From` header is the bare address. | `''` |

## Notifications

| Variable | Description | Default |
|---|---|---|
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-...`) used to send Slack notifications. The Slack app needs the `chat:write`, `users:read` and `users:read.email` scopes. Without it, Slack notifications are not sent. | unset |
| `WEBHOOK_URL` | Read into the configuration but not used. Webhook targets are set per notification event or event rule in the UI. | `''` |

## Authentication

| Variable | Description | Default |
|---|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID for SSO. | `''` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret. | `''` |
| `AZURE_OAUTH_TENANT_ID` | Entra ID tenant ID, for Microsoft SSO, the Entra ID user sync and the Microsoft 365 connector. Must be a single tenant. | `''` |
| `AZURE_OAUTH_CLIENT_ID` | Entra ID application (client) ID. | `''` |
| `AZURE_OAUTH_CLIENT_SECRET` | Entra ID client secret. | `''` |
| `ATLASSIAN_ALLOWED_HOSTS` | Comma-separated hosts, besides `*.atlassian.net`, that the Atlassian connector may use as its Site URL. | `''` |
| `OAUTHLIB_INSECURE_TRANSPORT` | Set to `1` to allow OAuth over plain HTTP. **Development only**: it also turns off HTTPS redirection. | unset |
| `MFA_ENABLED` | Email a one-time code when a user signs in from an unknown IP address. Set to `True` to enable. | `False` |

## Content Security Policy

| Variable | Description | Default |
|---|---|---|
| `CSP_ENABLED` | Send the `Content-Security-Policy` header. Set to `False` to turn it off entirely. | `True` |
| `CSP_REPORT_ONLY` | Send the policy as `Content-Security-Policy-Report-Only`, so violations are logged in the browser console without being blocked. Useful to check a change before enforcing it. | `False` |

## Session cookies

The session cookie flags are not read from the environment. flask-talisman sets them when the app starts:

| Flag | Value |
|---|---|
| `Secure` | On, except when the app runs in debug mode |
| `HttpOnly` | On |
| `SameSite` | `Lax` |

`.env.example` still lists `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY` and `SESSION_COOKIE_SAMESITE`, but setting them has no effect.

## Container startup

These are read by the container entrypoint (`entrypoint.sh`), not by the app. Both must be exactly `True` to take effect.

| Variable | Description | Default |
|---|---|---|
| `SEED_DEMO_DATA` | Seed demo data (users, assets, risks and so on) on startup. Development only. | `False` |
| `ENTERPRISE_ENABLED` | Seed the Enterprise plugin's data on startup when the plugin is present in `/app/opsdeck-enterprise`. The plugin itself is loaded whenever it is installed, whatever this is set to. | `False` |

!!! tip "Minimal production `.env`"
    ```bash
    SECRET_KEY=<64-char random string>
    DATA_ENCRYPTION_KEY=<Fernet key>
    DATABASE_URL=postgresql://opsdeck:password@db:5432/opsdeck
    FLASK_APP=run:app
    FLASK_DEBUG=0
    APP_BASE_URL=https://opsdeck.yourcompany.com
    TRUST_PROXY=1
    DEFAULT_ADMIN_EMAIL=admin@yourcompany.com
    DEFAULT_ADMIN_INITIAL_PASSWORD=<strong password>
    ```

    Generate a Fernet key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Set `TRUST_PROXY=1` only when a reverse proxy sits in front of OpsDeck.
