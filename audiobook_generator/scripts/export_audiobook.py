#!/usr/bin/env python
# File: export.py
"""
export.py – Export the AudioBookApp as a static website, optionally generating images for each page.

Usage:
    python export.py <input_file> <output_directory> [--with_image]

Arguments:
    <input_file>        Path to the text file containing the audiobook content
    <output_directory>  Path to the directory where the static site will be generated

Options:
    --with_image        If provided, will attempt to generate an image for each page using the OpenAI API.

When run (for example “python export.py data/input.txt chapter1/ --with_image”) it:
  • Instantiates the AudioBookGenerator to load and generate audio files.
  • If --with_image is provided, also calls the OpenAI Image Generation API for each page to generate an image.
  • Instantiates the AudioBookApp (which builds routes for page “/0”, “/1”, etc.)
  • Uses Starlette’s TestClient to get the rendered HTML for each page.
  • Fixes the generated URLs so that href="/0" becomes "index.html" for page 0 and "1.html" for page 1, etc.
  • Writes each page into the output folder.
  • Copies the assets (such as audio files and/or images) to an "assets" subfolder.
  
After exporting, opening the output folder’s index.html will display your audiobook (and images if generated).
"""

import argparse
import re
import shutil
from pathlib import Path

# --- Import FastHTML and Starlette classes
from fasthtml.common import *

# --- For text processing and TTS
from audiobook_generator.audiobook_app import AudioBookApp
from audiobook_generator.audiobook_generator import AudioBookGenerator

# --- For image generation


def main():
    parser = argparse.ArgumentParser(description="Export AudioBook as static website")
    parser.add_argument("input_file", type=str, help="Path to the input text file")
    parser.add_argument(
        "output_directory", type=str, help="Path to the output directory"
    )
    parser.add_argument(
        "--with_image",
        action="store_true",
        help="Generate an AI image for each page using OpenAI",
    )
    parser.add_argument(
        "--book_name",
        type=str,
        default="AudioBook",
        help="Name of the book to display in the browser tab",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Exporting to {output_dir.resolve()}")

    # Instantiate and prepare the audiobook
    if args.input_file.endswith(".md"):
        audio_book = AudioBookGenerator.from_large_md(args.input_file)
    else:
        audio_book = AudioBookGenerator.from_txt(args.input_file)
    # audio_book.load_text()
    audio_book.generate_audio()

    # If user wants images, generate them now
    if args.with_image:
        audio_book.generate_images()

    # Create the app instance
    audio_book_app = AudioBookApp(audio_book, args.book_name)
    app = audio_book_app.app

    # Use Starlette's TestClient to simulate requests and render pages
    from starlette.testclient import TestClient

    client = TestClient(app)

    num_pages = len(audio_book.items)
    print(f"Found {num_pages} page(s) to export.")

    # For each page route, fetch HTML and post-process links so they work as static files.
    for idx in range(num_pages):
        route = f"/{idx}"
        response = client.get(route)
        html = response.text

        # Replace href="/<number>" with relative file links.
        def repl_href(match):
            num = match.group(1)
            return 'href="index.html"' if num == "0" else f'href="{num}.html"'

        html = re.sub(r'href="/(\d+)"', repl_href, html)

        # Replace src="/assets/" with src="assets/" (remove the leading slash)
        html = re.sub(r'src="/assets/', 'src="assets/', html)

        # Write output file (page 0 becomes index.html, others become {idx}.html)
        filename = "index.html" if idx == 0 else f"{idx}.html"
        file_path = output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Written {file_path}")

    # Copy the assets directory (audio files and any generated images) to the export folder.
    assets_src = audio_book.assets_dir
    assets_dest = output_dir / "assets"
    if assets_src.exists():
        if assets_dest.exists():
            shutil.rmtree(assets_dest)
        shutil.copytree(assets_src, assets_dest)
        print(f"Copied assets from {assets_src} to {assets_dest}")
    else:
        print("No assets directory found to copy.")

    print(
        f"Export complete. Open {output_dir.resolve()}/index.html to view the audiobook."
    )


if __name__ == "__main__":
    main()
