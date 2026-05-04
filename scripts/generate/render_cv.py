#!/usr/bin/env python3
"""Render a markdown CV to PDF."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fu7ur3pr00f.generators import render_cv_pdf


def main():
    if len(sys.argv) < 2:
        print("Usage: python render_cv.py <path/to/cv.md>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"File not found: {md_path}")
        sys.exit(1)

    print(f"Rendering PDF from {md_path}...")
    pdf_path = render_cv_pdf(md_path)
    print(f"PDF generated: {pdf_path}")


if __name__ == "__main__":
    main()
