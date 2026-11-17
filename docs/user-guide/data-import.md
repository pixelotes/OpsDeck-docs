# Data Import (CLI)

OpsDeck provides CLI commands for bulk CSV import, useful for initial system bootstrapping or migrating from legacy tools. The commands use the same import engine and rules as **Administration > Import Data** in the UI, which also offers a preview and a downloadable template for each type.

## General usage

All import commands use the Flask CLI: `flask data-import <type> <file.csv>`. For Docker Compose deployments:

```bash
# Copy the CSV into the container
docker compose cp my_data.csv web:/app/my_data.csv

# Run the import
docker compose exec web flask data-import users /app/my_data.csv
```

For local installations, run directly (with `FLASK_APP=run:app` set, for example in `.env`):

```bash
flask data-import users my_data.csv
```

List the available types, and the columns each one takes, with:

```bash
flask data-import --help
flask data-import assets --help
```

## CSV format

- The first row is the header. Column names must match the names below exactly.
- Required columns must be present; a missing required column stops the import before any row is read. Optional columns can be left out.
- Files are read as UTF-8 (a byte order mark, as written by Excel, is accepted).
- At most 5,000 rows per import.

## Supported types

| Type | Required columns | Optional columns | Notes |
|---|---|---|---|
| `users` | `name`, `email` | — | New users get the `user` role and a generated password, printed once at the end of the run. Existing emails are skipped. |
| `suppliers` | `name` | `email`, `phone`, `address`, `website`, `compliance_status`, `owner` | Existing names are skipped. `owner` is an active user's email or a group name. |
| `contacts` | `name`, `supplier_name` | `email`, `phone`, `role` | The supplier is matched by name and created if missing. |
| `assets` | `name`, `serial_number` | `brand`, `model`, `status`, `location_name`, `assigned_user`, `purchase_date`, `cost`, `warranty_length` | Brand, model and location are matched by name and created if missing. `assigned_user` (by name) creates a checkout. Existing serial numbers are skipped. |
| `peripherals` | `name`, `serial_number` | `type`, `brand`, `status`, `location_name`, `assigned_user` | Brand and location are matched by name and created if missing. `assigned_user` creates a checkout. |
| `software` | `name` | `category`, `description`, `supplier_name`, `owner_email`, `iso_27001_controls` | Existing names are skipped. Supplier and owner are linked when found. |
| `subscriptions` | `supplier_name`, `name` | `type`, `cost`, `currency`, `renewal_date`, `period_type`, `period_value`, `software_name`, `budget_name`, `assigned_user_email`, `auto_renew`, `description` | The supplier must already exist. Software, budget and user are linked when found. |
| `risks` | `name` | `likelihood`, `impact`, `description`, `category` | `likelihood` and `impact` are 1–5 (default 1). `category` is a comma-separated list. |
| `locations` | `name` | `address`, `city`, `zip_code`, `country`, `timezone` | Existing names are skipped. |
| `tags` | `name` | — | Existing names are skipped. |
| `brands` | `name` | `website`, `notes` | Existing names are skipped. |
| `asset_models` | `name`, `brand` | — | The brand is matched by name and created if missing. |
| `cost_centers` | `code`, `name` | `description` | Existing codes are skipped. |
| `budgets` | `name`, `amount` | `category`, `currency`, `period`, `valid_from`, `valid_until` | Existing names are skipped. `valid_from` and `valid_until` default to the current year. |
| `payment_methods` | `name`, `method_type` | `details`, `expiry_date` | Existing names are skipped. |

Dates use the `YYYY-MM-DD` format, as in the templates offered by the Import Data screen.

## Validation and error handling

- Each row is classified as created, skipped (for example a duplicate) or error. One bad row does not stop the others.
- Rows that were skipped or failed are printed with their row number and the reason.
- All created rows are saved together at the end of the run.
- The last line is a summary: created, skipped and error counts.

## Helper scripts

The `scripts/` directory of the repository holds standalone scripts that run outside OpsDeck, typically from a workstation or a scheduled job. Each script has its own `.md` file next to it with the full reference.

| Script | Direction | What it does |
|---|---|---|
| `google-import.py` | Google Workspace → OpsDeck | Creates OpsDeck users for Google Workspace accounts that are not in OpsDeck yet |
| `google-provision.py` | OpsDeck → Google Workspace | Creates or suspends Google Workspace accounts from pending onboardings and offboardings |
| `jira-sync.py` | Jira → OpsDeck | Creates or updates changes, incidents and onboardings from Jira issues |
| `bcdr-export.py` | Database → Excel | Exports the whole database to one Excel file per entity, for offline copies |

The three integration scripts talk to OpsDeck through its [REST API](api.md) with an API token from a user profile; they need no database access. `bcdr-export.py` reads the database directly.

### google-import.py

Reads users from Google Workspace through the Admin Directory API and creates the ones that do not exist in OpsDeck yet, through `POST /api/v1/users`. Existing users, matched by email, are left untouched, so the script can run repeatedly, for example as a Kubernetes CronJob.

```bash
pip install requests google-auth google-api-python-client
```

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Path to the service account JSON key |
| `GOOGLE_DELEGATED_USER` | Yes | Google admin email the service account acts as (domain-wide delegation) |
| `OPSDECK_URL` | Yes | OpsDeck base URL, such as `https://opsdeck.internal` |
| `OPSDECK_API_TOKEN` | Yes | OpsDeck API token |
| `GOOGLE_DOMAIN` | No | Only import users whose email ends with `@<domain>` |
| `OPSDECK_DEFAULT_ROLE` | No | Role given to imported users. Default `user` |

| Option | Description |
|---|---|
| `--org-unit /PATH` | Only import users in this organizational unit and its sub-units. Default: all users |
| `--include-suspended` | Also import suspended Google accounts. Default: skip them |
| `--dry-run` / `--execute` | Preview, or create the users. One of the two is required |

```bash
python scripts/google-import.py --org-unit /Employees --dry-run
python scripts/google-import.py --org-unit /Employees --execute
```

Imported users get their name, email, the default role and, when Google has them, department and job title. They have no password and sign in with SSO, unless you set one. The service account needs the read-only scope `https://www.googleapis.com/auth/admin.directory.user.readonly`.

### google-provision.py

Reads pending onboardings and offboardings from OpsDeck and creates or suspends the matching Google Workspace accounts.

```bash
pip install requests google-auth google-api-python-client
```

It takes the same four required variables as `google-import.py`, plus the optional `GOOGLE_ORG_UNIT` (organizational unit for new accounts, default `/`) and `GOOGLE_DOMAIN` (skip emails outside this domain). Google credentials are only needed with `--execute`.

```bash
python scripts/google-provision.py provision --dry-run   # create accounts for pending onboardings
python scripts/google-provision.py suspend --execute     # suspend accounts for pending offboardings
python scripts/google-provision.py all --execute         # both
```

The first argument is `provision`, `suspend` or `all`, and one of `--dry-run` or `--execute` is required. New accounts get a random 24-character temporary password that must be changed at first sign-in. The service account needs the scope `https://www.googleapis.com/auth/admin.directory.user`.

!!! warning
    The script reads `/api/v1/onboardings/pending-provisioning` and `/api/v1/offboardings/pending-suspension` and posts to `.../mark-provisioned` and `.../mark-suspended`. The current OpsDeck API does not provide these endpoints, so the script fails against a standard installation.

### jira-sync.py

Reads issues from a Jira project, filtered by label and age, and creates or updates the matching OpsDeck records through the API. The Jira issue key is stored as `external_ref`, so running it again updates records instead of duplicating them.

```bash
pip install requests
```

| Variable | Required | Description |
|---|---|---|
| `JIRA_BASE_URL` | Yes | Jira URL, such as `https://yourorg.atlassian.net` |
| `JIRA_EMAIL` | Yes | Jira user email |
| `JIRA_API_TOKEN` | Yes | Jira API token |
| `OPSDECK_BASE_URL` | Yes | OpsDeck base URL. Note the name: this script uses `OPSDECK_BASE_URL`, the Google scripts use `OPSDECK_URL` |
| `OPSDECK_API_TOKEN` | Yes | OpsDeck API token |
| `JIRA_PROJECT` | No | Project key. Default `HELP` |
| `JIRA_LABEL` | No | Only issues with this label. Default `opsdeck-sync` |
| `JIRA_DAYS` | No | Only issues created in the last N days. Default `90` |

```bash
python scripts/jira-sync.py --dry-run   # show the payloads, write nothing
python scripts/jira-sync.py             # sync
```

| Jira issue type | OpsDeck record |
|---|---|
| `[System] Change` | Change (`POST /api/v1/changes`) |
| `[System] Incident` | Incident (`POST /api/v1/incidents`) |
| `Onboarding` | Onboarding (`POST /api/v1/onboardings`) |

Other issue types are reported as skipped. Jira priorities map to change priorities (Highest → Critical, High → High, Medium → Medium, Low and Lowest → Low) and to incident severities (Highest → SEV-0 down to Low and Lowest → SEV-3). Reporter and assignee are matched to OpsDeck users by email.

### bcdr-export.py

Exports all data from the OpsDeck database into a directory with one `.xlsx` file per entity type (users, assets, suppliers, risks, controls, policies and so on) plus an `_Index.xlsx` summary, for offline copies and disaster recovery. Attachments are listed as metadata only, and stored secrets are exported as they are stored, never in clear text. It does not replace a database backup; see [Backup & Restore](../deployment/backup-restore.md).

```bash
pip install sqlalchemy "psycopg[binary]" openpyxl
```

Every setting can be passed as a flag or an environment variable; flags win.

| Flag | Variable | Default | Description |
|---|---|---|---|
| `--database-url` | `DATABASE_URL` | built from the `POSTGRES_*` values | Full connection URL |
| `--host` | `POSTGRES_HOST` | `localhost` | Database host |
| `--port` | `POSTGRES_PORT` | `5432` | Database port |
| `--db` | `POSTGRES_DB` | `opsdeck` | Database name |
| `--user` | `POSTGRES_USER` | `opsdeck` | Database user |
| — | `POSTGRES_PASSWORD` | `opsdeck` | Database password. There is no flag, so the password does not show up in `ps` or shell history |
| `--output`, `-o` | `OUTPUT_DIR` | `bcdr_opsdeck_YYYYMMDD_HHMM/` | Output directory |
| — | `BCDR_OUTPUT_ROOT` | unset | When set, the output directory must be inside it, or the script stops with an error |

```bash
python scripts/bcdr-export.py --database-url "$DATABASE_URL" --output /backups/opsdeck
```

To run it inside the OpsDeck container, where SQLAlchemy and the PostgreSQL driver are already installed, add `openpyxl` first:

```bash
docker compose cp scripts/bcdr-export.py web:/tmp/bcdr-export.py
docker compose exec web pip install openpyxl
docker compose exec web python /tmp/bcdr-export.py --output /tmp/bcdr-export
docker compose cp web:/tmp/bcdr-export ./export
```

Inside the container `DATABASE_URL` is already set, so no connection flags are needed.
