#!/usr/bin/env python3
"""Pre-render Mermaid code blocks in Markdown files to SVG using mmdc.

Usage: python render-mermaid.py <docs-directory> [--puppeteer-config /path/to/config.json]

For each .md file containing ```mermaid blocks, this script:
1. Extracts each mermaid block to a temporary .mmd file
2. Runs mmdc to generate an SVG
3. Saves the SVG next to the .md file
4. Replaces the ```mermaid block with an ![diagram](path.svg) reference

This script is designed to run in CI before mkdocs build.
Use git checkout -- docs/ to revert changes after build.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MERMAID_BLOCK = re.compile(
    r'```mermaid\s*\n(.*?)```',
    re.DOTALL
)


def render_mermaid_blocks(docs_dir: str, puppeteer_config: str = None) -> int:
    docs_path = Path(docs_dir)
    total_rendered = 0
    total_failed = 0

    for md_file in sorted(docs_path.rglob('*.md')):
        content = md_file.read_text(encoding='utf-8')
        matches = list(MERMAID_BLOCK.finditer(content))

        if not matches:
            continue

        print(f"  {md_file.relative_to(docs_path)}: {len(matches)} diagram(s)")

        svg_dir = md_file.parent
        stem = md_file.stem

        new_content = content
        for i, match in enumerate(matches, 1):
            mermaid_code = match.group(1).strip()
            svg_name = f"{stem}-mermaid-{i}.svg"
            svg_path = svg_dir / svg_name

            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.mmd', delete=False, encoding='utf-8'
            ) as tmp:
                tmp.write(mermaid_code)
                tmp_path = tmp.name

            try:
                cmd = [
                    'mmdc',
                    '-i', tmp_path,
                    '-o', str(svg_path),
                    '-b', 'transparent',
                    '--quiet',
                ]
                if puppeteer_config:
                    cmd.extend(['-p', puppeteer_config])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0 or not svg_path.exists():
                    stderr = result.stderr.strip()[:200] if result.stderr else 'unknown error'
                    print(f"    WARNING: diagram {i} failed: {stderr}")
                    total_failed += 1
                    continue

                replacement = f'![Diagram {i}]({svg_name})'
                new_content = new_content.replace(match.group(0), replacement)
                total_rendered += 1
                print(f"    diagram {i} -> {svg_name}")

            except subprocess.TimeoutExpired:
                print(f"    WARNING: diagram {i} timed out")
                total_failed += 1
            finally:
                os.unlink(tmp_path)

        if new_content != content:
            md_file.write_text(new_content, encoding='utf-8')

    print(f"\nDone: {total_rendered} rendered, {total_failed} failed")
    return 1 if total_failed > 0 and total_rendered == 0 else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pre-render Mermaid diagrams to SVG')
    parser.add_argument('docs_dir', help='Path to docs directory')
    parser.add_argument('-p', '--puppeteer-config', help='Path to Puppeteer config JSON')
    args = parser.parse_args()

    sys.exit(render_mermaid_blocks(args.docs_dir, args.puppeteer_config))
