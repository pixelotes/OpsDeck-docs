# Frontend Stack

OpsDeck uses server-rendered Jinja2 templates with Bootstrap 5, enhanced by purpose-specific JavaScript libraries and a few small first-party scripts. There is no SPA framework and no JS bundler.

## Template architecture

Templates follow Jinja2's layout inheritance pattern:

```
templates/
├── layout.html              # Base layout: navbar, sidebar, footer, JS/CSS includes
├── components/              # Reusable includes and macros
│   ├── list_macros.html     # People, empty values and row actions in list tables
│   ├── empty_state.html     # "Nothing here yet" panel for empty lists
│   ├── skeleton_table.html  # Skeleton loaders (also _card, _list, _dashboard)
│   ├── back_button.html
│   ├── compliance_link_macro.html
│   ├── ticket_list.html
│   └── ...
└── [module]/                # One directory per functional module
    ├── list.html            # Table listing with filters
    ├── detail.html          # Entity detail view
    ├── form.html            # Create/edit form
    └── ...
```

All module templates extend `layout.html` and use `{% block content %}` for page-specific content. Reusable components are included via `{% include 'components/...' %}` or imported as macros.

## Shared components

### List macros

Every list table renders people, empty cells and row actions through `components/list_macros.html`, so all lists look and behave the same. Import it with context (the macros check permissions with `can_read`):

```jinja
{% import 'components/list_macros.html' as L with context %}
```

| Macro | Renders |
|---|---|
| `L.person(user_or_group, link=true)` | An initials avatar (or a group icon for groups) followed by the full name, linked to the user or group detail page when the viewer can read Administration. Renders `—` when empty |
| `L.empty()` | A single muted `—` for an empty value. Lists use it instead of `N/A`, `-`, `Unassigned` or `Unknown` |
| `L.actions()` | Wrapper for the row action buttons, used with `{% call %}` |
| `L.action_view(url)`, `L.action_edit(url)` | View and Edit buttons |
| `L.action_delete(url, confirm)` | Delete button (outline red) that posts through the confirmation dialog |
| `L.action_button(url, icon, title, ...)` | Any other action: a GET link, a POST form (`method='post'`, optional `confirm`), or a JS/modal button (`url=none` with `attrs`) |

Row actions are icon-only `btn-sm btn-outline-secondary` buttons (delete is `btn-outline-danger`), right-aligned in a column with the header `<th class="text-end">Actions</th>`, always in this order: view, edit, module-specific actions, delete.

```jinja
<td>{{ L.person(asset.user) }}</td>
<td>{{ asset.serial_number or L.empty() }}</td>
<td class="text-end">
    {% call L.actions() %}
        {{ L.action_view(url_for('assets.asset_detail', id=asset.id)) }}
        {% if can_write('assets') %}
        {{ L.action_edit(url_for('assets.edit_asset', id=asset.id)) }}
        {{ L.action_delete(url_for('assets.delete_asset', id=asset.id), "Delete asset '" ~ asset.name ~ "'?") }}
        {% endif %}
    {% endcall %}
</td>
```

### Empty state

`components/empty_state.html` shows an icon, a title, a message and an optional primary and secondary action button when a list has no rows. The page sets the variables before including it:

```jinja
{% set icon = 'building' %}
{% set title = 'No Suppliers Found' %}
{% set message = 'Add suppliers to manage vendor relationships and subscriptions.' %}
{% set action_url = url_for('suppliers.new_supplier') if can_write('procurement') else none %}
{% set action_text = 'Add First Supplier' %}
{% include 'components/empty_state.html' %}
```

Other parameters: `action_icon` (default `plus`), `secondary_url`, `secondary_text` and `secondary_icon`. `icon` is a Font Awesome name without the `fa-` prefix (default `inbox`); some lists pass a single emoji instead, which the component also accepts.

### Skeleton loaders

Placeholder shapes shown while a page or panel loads:

- **Templates**: `components/skeleton_table.html`, `skeleton_card.html`, `skeleton_list.html` and `skeleton_dashboard.html`. The compliance, risk, finance and asset dashboards include a skeleton and hide it once the page has loaded.
- **`static/js/skeleton.js`**: the global `Skeleton` object for content loaded with `fetch()`. `Skeleton.show(container, type, options)` replaces a container's content with a `table`, `card`, `list` or `dashboard` skeleton, `Skeleton.hide(container)` restores it, `Skeleton.wrap(container, asyncFn)` does both around an async call, and `Skeleton.inline(type)` returns the HTML of a single skeleton element.

## Bootstrap 5

Bootstrap 5 (loaded from `static/vendor/`) provides:

- Responsive grid system for layout.
- Form styling and validation states.
- Card components for detail views.
- Table styling (enhanced by Simple DataTables).
- Modal dialogs for confirmations and quick actions.

No custom Bootstrap build — the full distribution is used via `copy-assets.js`.

## First-party scripts

`layout.html` loads these on every page, from `static/js/`:

| Script | Purpose |
|---|---|
| `toast.js` | Toast notifications (see below) |
| `button-effects.js` | Button micro-interactions |
| `skeleton.js` | Skeleton loaders (see above) |

### Toasts

Feedback messages are shown by `toast.js`, a small custom script, not by the Bootstrap toast component.

- **Flash messages become toasts.** On page load, every Bootstrap alert with `role="alert"` (which is how Flask flash messages are rendered) is hidden and shown as a toast instead. The type comes from the alert class: `alert-success` → success, `alert-danger` → error, `alert-warning` → warning, anything else → info.
- **Types**: `success`, `error`, `warning`, `info` and `danger`, each with its own icon and colour.
- **Auto-dismiss** after 4 seconds by default. Each toast also has a close button. A duration of `0` keeps the toast until it is closed.
- **At most 5** toasts are shown at once; a new one dismisses the oldest.
- **API** for page scripts: `Toast.show(message, type, duration)`, the shortcuts `Toast.success()`, `Toast.error()`, `Toast.warning()`, `Toast.info()` and `Toast.danger()`, and `Toast.clearAll()`.

### Button effects

`button-effects.js` adds a ripple effect on click to every `.btn` that is not disabled (opt out with the `no-ripple` class), including buttons added to the page later. Buttons with a `data-pulse` attribute pulse for that many milliseconds (default 5000). Page scripts can use `ButtonEffects.shake(button)` (for example on a validation error), `ButtonEffects.pulse(button, duration)` and `ButtonEffects.setLoading(button, true|false)`, which disables the button and shows a loading state.

## JavaScript libraries

Each interactive need is solved by a purpose-specific library:

| Library | Version | Purpose | Where used |
|---|---|---|---|
| **Simple DataTables** | 10.3.x | Sortable, searchable, paginated tables | List views |
| **Tom Select** | 2.6.x | Enhanced select inputs with search and tagging | Entity selection dropdowns |
| **Chart.js** | 4.6.x | Dashboard charts and visualizations | Dashboard, reports, compliance drift |
| **SimpleCalendarJS** (`simple-calendar-js`) | 3.0.x | Calendar views | Renewal calendar |
| **Mermaid** | 12.2.x | Diagram rendering from Markdown-like syntax | Service topology, documentation |
| **SunEditor** | 3.4.x | Rich text editor (WYSIWYG) | Description fields, notes |
| **EasyMDE** | 2.21.x | Markdown editor | Documentation pages |
| **SortableJS** | 1.15.x | Drag-and-drop reordering | Onboarding pack items, priority lists |
| **Swagger UI** | 5.34.1 | Interactive API documentation | `/swagger-ui` endpoint |
| **html2canvas** | 1.4.x | Client-side screenshots | Report generation |
| **OrgChart.js** | 0.0.4 | Organization chart rendering | HR & People → Org Chart |
| **Font Awesome** | 7.3.x | Icons throughout the UI | Global |

## Asset pipeline

There is no Webpack, Vite, or other bundler. The asset pipeline is a simple Node.js script:

```bash
npm install        # Install packages to node_modules/
npm run build-assets  # Copies vendor files to src/static/vendor/
```

`copy-assets.js` copies the required distribution files (minified JS and CSS) of each package to `src/static/vendor/`. Templates load these files with standard `<script>` and `<link>` tags, so every library must ship a build that works from a plain script tag (a global or IIFE bundle). ESM-only libraries cannot be used without adding a bundler. The Docker image runs this step in a separate Node build stage.

## JavaScript patterns

Client-side JavaScript follows these conventions:

- **No module bundling.** Scripts are loaded globally via `<script src="...">` tags.
- **Progressive enhancement.** Core functionality works without JavaScript. JS adds interactivity (search, sort, AJAX updates) on top.
- **AJAX for partial updates.** Some actions (status toggles, inline edits, bulk operations) use `fetch()` to call route endpoints and update the DOM without full page reloads.
- **Event delegation.** Table-level event handlers manage clicks on dynamically rendered rows.
