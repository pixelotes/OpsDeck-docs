# Dependencies

Complete list of Python and JavaScript dependencies used by OpsDeck, with version and purpose.

## Python dependencies

### Production (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| **Flask** | 3.1.3 | Web framework — lightweight, blueprint-based, extension-friendly |
| **Flask-SQLAlchemy** | 3.1.1 | SQLAlchemy integration for Flask — session management, model base class |
| **Flask-Migrate** | 4.1.0 | Database migrations via Alembic — schema versioning and upgrades |
| **Flask-Login** | 0.6.3 | Session-based user authentication — login/logout, remember-me, session protection |
| **Flask-Dance** | 7.1.0 | OAuth provider integration — Google and Microsoft Entra ID SSO |
| **Flask-WTF** | 1.3.0 | Form handling with CSRF protection |
| **flask-talisman** | 1.1.0 | Security headers — CSP, HSTS, X-Frame-Options, HTTPS redirection, session cookie flags |
| **flask-smorest** | 0.47.0 | REST API framework — OpenAPI spec generation, request/response validation |
| **Flask-Limiter** | 4.1.1 | Rate limiting — brute-force protection, API throttling |
| **marshmallow-sqlalchemy** | 1.5.0 | Auto-schema generation from SQLAlchemy models for API serialization |
| **SQLAlchemy** | *(transitive, 2.1)* | ORM — model definition, querying, relationship management |
| **Alembic** | *(transitive)* | Migration engine — auto-detect model changes, generate migration scripts |
| **psycopg[binary]** | 3.3.9 | PostgreSQL driver (psycopg 3). SQLAlchemy 2.1 uses it for plain `postgresql://` URLs, so `DATABASE_URL` needs no driver suffix. The binary package bundles `libpq`, so no system PostgreSQL libraries or compiler are needed |
| **APScheduler** | 3.11.3 | Background job scheduler — cron-style jobs, in-process execution |
| **gunicorn** | 26.2.0 | Production WSGI server — multi-worker, pre-fork model |
| **requests** | 2.34.2 | HTTP client — webhook delivery, API connectors, external API calls |
| **python-dateutil** | 2.9.0.post0 | Date parsing and manipulation — relative deltas, recurring dates |
| **python-dotenv** | 1.2.3 | Loads `.env` files for the `flask` command |
| **pytz** | 2026.3.post1 | Timezone definitions — IANA timezone database |
| **MarkupSafe** | 3.0.3 | HTML escaping — Jinja2 dependency, XSS prevention |
| **Markdown** | 3.10.3 | Markdown rendering — documentation pages, rich text descriptions |
| **bleach** | 6.4.0 | HTML sanitization — cleans user-supplied rich text and rendered Markdown before display |
| **WeasyPrint** | 70.0 | HTML-to-PDF rendering — report generation using existing templates |
| **ecs-logging** | 2.3.0 | ECS-format structured logging — Elasticsearch-compatible log format |
| **deepdiff** | 9.1.0 | Structured object comparison — UAR engine, connector report diffs |
| **slack_sdk** | 3.44.0 | Slack API client — notification delivery to Slack channels |
| **PyJWT** | 2.14.0 | JWT handling — signs the service-account token for the Google Workspace connector |
| **cryptography** | 50.0.0 | Fernet encryption of stored secrets (API connector credentials), key derivation |
| **boto3** | 1.43.83 | AWS SDK — AWS API connector |

### Development (`requirements-dev.txt`)

`requirements-dev.txt` includes `requirements.txt` and adds:

| Package | Version | Purpose |
|---|---|---|
| **pytest** | 9.1.1 | Test framework |
| **pytest-cov** | 7.1.0 | Coverage reports |
| **pytest-randomly** | 4.1.0 | Runs tests in random order to catch hidden dependencies between them |
| **Faker** | 40.37.0 | Fake data generation — test fixtures, demo data seeding |
| **ruff** | 0.16.5 | Linter (configured in `pyproject.toml`) |

## JavaScript dependencies

### Production (`package.json`)

| Package | Version | Purpose |
|---|---|---|
| **bootstrap** | 5.3.x | CSS framework — responsive grid, components, utilities |
| **@popperjs/core** | 2.11.x | Tooltip/popover positioning — Bootstrap dependency |
| **@fortawesome/fontawesome-free** | 7.3.x | Icon library — UI icons throughout the application |
| **chart.js** | 4.6.x | Chart library — dashboard visualizations, compliance trends |
| **simple-datatables** | 10.3.x | Table enhancement — sort, search, paginate HTML tables |
| **tom-select** | 2.6.x | Enhanced select inputs — search, tagging, remote data |
| **simple-calendar-js** | 3.0.x | Calendar component (SimpleCalendarJS) — renewal calendar |
| **mermaid** | 12.2.x | Diagram renderer — service topology, flowcharts from text |
| **suneditor** | 3.4.x | WYSIWYG editor — rich text editing for descriptions and notes |
| **easymde** | 2.21.x | Markdown editor — documentation editing with preview |
| **sortablejs** | 1.15.x | Drag-and-drop — reorderable lists (onboarding items, priorities) |
| **swagger-ui-dist** | 5.34.1 | API documentation UI — interactive endpoint testing (pinned to an exact version) |
| **html2canvas** | 1.4.x | DOM-to-canvas screenshot — client-side report captures |
| **orgchart.js** | 0.0.4 | Organization chart — hierarchical user visualization |

## Dependency management

Python dependencies are pinned to exact versions (`==`) in `requirements.txt` and `requirements-dev.txt` for reproducible builds. The `update-deps.sh` script automates the update workflow, using the existing `venv/`:

1. Strips the version pins from both files.
2. Installs the latest versions of every package.
3. Freezes the result and writes the new pins back into `requirements.txt` and `requirements-dev.txt`.
4. Shows the diff and runs the test suite to verify compatibility.

JavaScript dependencies are managed via npm. `update-node-deps.sh` updates `package.json` with `npm-check-updates`, reinstalls and rebuilds the vendor assets. `copy-assets.js` (`npm run build-assets`) copies distribution files from `node_modules` to `src/static/vendor/` — no bundler involved.
