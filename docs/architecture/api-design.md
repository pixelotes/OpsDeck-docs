# API Design

OpsDeck has two JSON layers that work differently:

- **The REST API** (`/api/v1/`) is built with flask-smorest, which provides OpenAPI (Swagger) spec generation, request validation, and response serialization. It authenticates with bearer tokens and is the contract for third-party integrations.
- **In-app JSON endpoints** live in the module blueprints and serve the application's own JavaScript (TomSelect remote sources, the calendar feed, kanban drag and drop, the Gantt chart). They use the browser session, have no versioning, schemas or Swagger entry, and share their error conventions through `src/utils/json_api.py`.

## Architecture

```
src/api.py              # REST API blueprint, token auth hook, resources
src/schemas.py          # Marshmallow schemas (auto-generated from SQLAlchemy models) and input schemas
src/utils/json_api.py   # json_endpoint / api_endpoint and request_wants_json for in-app JSON endpoints
```

The REST API blueprint is registered at `/api/v1/` with a `before_request` hook that validates bearer tokens on every request. The global login guard lets `/api/v1` paths through without a session, because they authenticate by token.

## REST conventions

| Verb | Usage |
|---|---|
| `GET /api/v1/{resource}` | List entities (`limit`/`offset`) |
| `GET /api/v1/{resource}/{id}` | Get single entity (404 if missing) |
| `POST /api/v1/{resource}` | Create or update (upsert) |

| Resource | GET list + detail | POST |
|---|---|---|
| `users` | Yes | Yes, upsert by `email` |
| `assets`, `peripherals`, `licenses`, `subscriptions`, `services`, `suppliers`, `contacts` | Yes | No |
| `changes`, `requests` | Yes | Yes, upsert by `external_ref` |
| `incidents`, `onboardings` | No | Yes, upsert by `external_ref` |

Read-only resources are registered with the `register_read_only_resource()` helper. Writable resources are `MethodView` classes that validate input with a dedicated input schema (`ChangeInputSchema`, `RequestInputSchema`, `IncidentInputSchema`, `OnboardingInputSchema`, `UserInputSchema`). Input schemas take people as an email or name (`requester`, `assignee`, `owner`, ...), resolved to active users by `resolve_user()`. A create returns 201 and an update 200. See [REST API](../user-guide/api.md) for the payloads.

## Authentication

Bearer token in the `Authorization` header. The `check_token()` hook:

1. Extracts the token from `Authorization: Bearer <token>`.
2. Looks up the user by token value (`User.api_token`, a `secrets.token_hex(32)` value stored as-is).
3. Sets `g.api_user` for the request context.
4. Returns a JSON 401 if the token is missing or invalid.
5. Logs all access attempts (success and failure) in ECS format.

The REST API does not apply module permissions; any valid token can call every endpoint.

## Marshmallow schemas

Output schemas are auto-generated from SQLAlchemy models using `marshmallow-sqlalchemy`:

```python
class AssetSchema(BaseSchema):
    custom_properties = fields.Dict(dump_only=True)
    class Meta(BaseSchema.Meta):
        model = Asset
```

This provides:

- Automatic field mapping from model columns, including foreign keys (`include_fk = True`).
- Exclusion of sensitive fields (`password_hash`, `api_token` on UserSchema).
- JSON serialization of complex types (dates, enums).
- Custom properties exposed as a flat dict.

## OpenAPI spec

flask-smorest auto-generates an OpenAPI 3.0.2 spec from the registered blueprint and schemas. Available to signed-in users at:

- `/openapi.json` — raw spec.
- `/swagger-ui` — interactive documentation UI (Swagger UI, served from vendored assets).

## Pagination

List endpoints accept `limit` (default 100) and `offset` (default 0) query parameters and return a plain JSON array. There is no envelope, total count or maximum page size. flask-smorest's `@paginate` is not used.

```
GET /api/v1/assets?limit=50&offset=100
```

## In-app JSON endpoints

A view declares that it answers JSON with a decorator from `src/utils/json_api.py`:

| Decorator | Effect |
|---|---|
| `@json_endpoint` | Marks the view as JSON. Authentication and permission failures are answered as JSON. |
| `@api_endpoint` | Implies `json_endpoint`, and also turns `BadRequest`, `ValueError` and `TypeError` into a JSON 400 and other exceptions into a JSON 500 (after a rollback and a logged stack trace). |

For a marked view:

- An unauthenticated call gets `401 {"error": "Authentication required."}` from the global login guard instead of a 302 to the login page.
- A missing module permission gets `403 {"error": "No access to the <module> module."}`, and read-only access to a write route gets `403 {"error": "Read-only access to the <module> module."}`, instead of a flash message and redirect.

`request_wants_json()` decides whether a request gets JSON. It checks, in order: the view's `json_endpoint` mark, `/api/` in the path, an `Accept` header whose best match is `application/json`, and finally a JSON body or the `X-Requested-With: XMLHttpRequest` header. The last two cover requests that never reach a view (a 404) and routes that serve both a form and AJAX, which cannot be marked without breaking the browser flow.

Error bodies always have the shape `{"error": "<message>"}`.

## Error pages

The application error handlers use `request_wants_json()` too, so a JSON caller gets a JSON body instead of an HTML page:

| Status | JSON body |
|---|---|
| 403 | `{"error": "Forbidden."}` |
| 404 | `{"error": "Not found."}` |
| 413 | `{"error": "That file is too large. The limit is <n> MB."}` |
| 429 | `{"error": "<rate limit description>"}` |
| 500 | `{"error": "Internal error."}` |

The 500 body deliberately omits the exception text. Rate-limit breaches and internal errors are also logged as audit events in the structured (ECS) application log.
