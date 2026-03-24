# OpsDeck Documentation

Source for the [OpsDeck documentation site](https://pixelotes.github.io/opsdeck-docs/).

Built with [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

## Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

The site will be available at `http://127.0.0.1:8000` with live reload.

## Build

```bash
mkdocs build
```

Static output goes to `site/`.

## PDF export

```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```

PDF is written to `site/export/opsdeck-docs.pdf`. Requires system packages for WeasyPrint (`libpango`, `libcairo`, etc.).

## CI/CD

- **Push to `main`** → Builds and deploys to GitHub Pages automatically.
- **Create a release** → Builds PDF and attaches it to the release as an asset.
- **Manual trigger** → Both workflows can be triggered via `workflow_dispatch`.

## Structure

```
docs/
├── index.md                  # Landing page
├── user-guide/               # End-user documentation by module
│   ├── index.md
│   ├── getting-started.md
│   ├── assets.md
│   ├── compliance.md
│   └── ...
├── deployment/               # Installation and operations
│   ├── index.md
│   ├── quickstart.md
│   ├── docker.md
│   ├── kubernetes.md
│   └── ...
├── architecture/             # Technical reference and ADRs
│   ├── index.md
│   ├── overview.md
│   ├── data-model.md
│   ├── decisions.md
│   └── ...
├── faq.md
└── changelog.md
```

## License

Documentation content follows the same [Elastic License](https://github.com/pixelotes/opsdeck/blob/main/LICENSE) as the main project.
