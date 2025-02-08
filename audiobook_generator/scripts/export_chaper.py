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
import sys
import os
import re
import shutil
from pathlib import Path

# --- Import FastHTML and Starlette classes
from fasthtml.common import *
from starlette.responses import FileResponse, RedirectResponse
from starlette.exceptions import HTTPException
from loguru import logger
from tqdm import tqdm

# --- For text processing and TTS
from audiobook_generator.audiobook_generator import AudioBookGenerator
from audiobook_generator.chatgpt_format_text import (
    raw_text_to_paragraphs,
    md_formated_llm,
)
from audiobook_generator.chunk_to_pages import chunk_into_pages
from audiobook_generator.text2wav import TextToSpeech

# --- For image generation
import requests


class AudioBookApp:
    def __init__(self, audio_book):
        self.audio_book = audio_book
        self.app, self.rt = fast_app(
            pico=True,
            hdrs=(
                MarkdownJS(),  # Required for rendering markdown
                Style(
                    """
/* ----- Theme Variables ----- */
/* Default (Light) Theme */
:root {
    --bg-color: #f9f9f9;
    --text-color: #333333;
    --header-bg: linear-gradient(90deg, #4a90e2, #9013fe);
    --header-text: #ffffff;
    --container-bg: #ffffff;
    --link-primary-bg: #4a90e2;
    --link-primary-text: #ffffff;
    --link-secondary-bg: #cccccc;
    --link-secondary-text: #333333;
}

/* Dark Theme Overrides */
body.dark {
    --bg-color: #1e1e1e;
    --text-color: #dddddd;
    --header-bg: linear-gradient(90deg, #222222, #555555);
    --header-text: #ffffff;
    --container-bg: #2e2e2e;
    --link-primary-bg: #009688;
    --link-primary-text: #ffffff;
    --link-secondary-bg: #444444;
    --link-secondary-text: #dddddd;
}

/* ----- Global Styles ----- */
body {
    background: var(--bg-color);
    color: var(--text-color);
    font-family: 'Helvetica Neue', Arial, sans-serif;
    margin: 0;
    padding: 0;
}

/* Header with Theme Toggle */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1em;
    background: var(--header-bg);
    color: var(--header-text);
}
.header h1 {
    margin: 0;
    font-size: 1.5em;
}
.theme-toggle {
    display: flex;
    gap: 0.5em;
}
.theme-toggle button {
    background: transparent;
    border: 1px solid var(--header-text);
    color: var(--header-text);
    padding: 0.3em 0.6em;
    border-radius: 4px;
    cursor: pointer;
}
.theme-toggle button.active {
    background: var(--header-text);
    color: var(--header-bg);
}

/* Main Content Container with Page-Turning Effect */
.container {
    max-width: 800px;
    margin: 2em auto;
    padding: 1.5em;
    background: var(--container-bg);
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    animation: pageTurn 0.8s ease;
    transform-style: preserve-3d;
}

/* Page Turning Animation */
@keyframes pageTurn {
    from {
        transform: perspective(600px) rotateY(90deg);
        opacity: 0;
    }
    to {
        transform: perspective(600px) rotateY(0deg);
        opacity: 1;
    }
}

/* Markdown Styling */
.marked {
    line-height: 1.6;
    font-size: 1.1em;
    margin-bottom: 1em;
}

/* Audio Player */
audio {
    display: block;
    margin: 1em auto;
}

/* Navigation Buttons */
nav a {
    font-size: 1.1em;
    text-decoration: none;
    padding: 0.5em 1em;
    border-radius: 4px;
    transition: background 0.3s;
}
nav a.secondary {
    background: var(--link-secondary-bg);
    color: var(--link-secondary-text);
}
nav a.primary {
    background: var(--link-primary-bg);
    color: var(--link-primary-text);
}
nav a:hover {
    opacity: 0.8;
}

/* ----- Theme Toggle Script ----- */
                    """
                ),
                Script(
                    """
function setTheme(theme) {
    if (theme === 'auto') {
        // Auto-detect based on prefers-color-scheme
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.className = 'dark';
        } else {
            document.body.className = 'light';
        }
    } else {
        document.body.className = theme;
    }
    localStorage.setItem('theme', theme);
    updateThemeToggle(theme);
}

function updateThemeToggle(theme) {
    var buttons = document.querySelectorAll('.theme-toggle button');
    buttons.forEach(function(btn) {
         if(btn.textContent.toLowerCase() === theme) {
              btn.classList.add('active');
         } else {
              btn.classList.remove('active');
         }
    });
}

window.addEventListener('load', function(){
    var storedTheme = localStorage.getItem('theme') || 'auto';
    setTheme(storedTheme);
});
                    """
                ),
            ),
            static_path="./assets",
            debug=True,
        )
        self.setup_routes()

    def setup_routes(self):
        # Home route simply redirects to page "0"
        @self.rt("/")
        def home():
            return RedirectResponse("/0")

        # Static assets – these will be copied in the export process
        @self.rt("/assets/{fname:path}")
        def static_assets(fname: str):
            path = self.audio_book.assets_dir / fname
            if path.exists():
                logger.info(f"Serving file: {path}")
                return FileResponse(path)
            logger.error(f"File not found: {path}")
            raise HTTPException(status_code=404, detail="File not found")

        # Page route: show the audiobook page for the given index.
        @self.rt("/{idx:int}")
        def page(idx: int):
            if not 0 <= idx < len(self.audio_book.items):
                logger.error(f"Invalid page index: {idx}")
                raise HTTPException(status_code=404, detail="Page not found")

            item = self.audio_book.items[idx]
            # Use NotStr() so that the pre-formatted markdown is rendered as HTML.
            # Using 'marked' class so MarkdownJS() can process it in the browser.
            text_markdown = Div(NotStr(item["text_md"]), cls="markdown marked")

            # If an image is generated or provided, display it
            image_content = Div()
            if "image" in item:
                image_content = ft_hx(
                    "img",
                    src=f"/assets/{item['image']}",
                    alt="Generated Image",
                    style="max-width:100%; margin-bottom:1em;",
                )

            # The audio player: note the src uses "/assets/...", which is post-processed in export.
            audio_player = ft_hx(
                "audio", controls=True, autoplay=True, src=f"/assets/{item['audio']}"
            )

            nav_links = self._create_navigation(idx)
            navigation = Div(
                *nav_links,
                cls="nav",
                style="display:flex; justify-content:space-between; margin-top:1em;",
            )

            header_div = Div(
                H1("My Audiobook"),
                Div(
                    Button("Light", onclick="setTheme('light');"),
                    Button("Dark", onclick="setTheme('dark');"),
                    Button("Auto", onclick="setTheme('auto');"),
                    cls="theme-toggle",
                ),
                cls="header",
            )
            content = Div(
                image_content, text_markdown, audio_player, navigation, cls="container"
            )
            return Titled(
                f"Page {idx+1} of {len(self.audio_book.items)}", header_div, content
            )

    def _create_navigation(self, idx):
        nav = []
        if idx > 0:
            nav.append(A("⟵ Previous", href=f"/{idx-1}", cls="secondary"))
        if idx < len(self.audio_book.items) - 1:
            nav.append(A("Next ⟶", href=f"/{idx+1}", cls="primary"))
        return nav

    def run(self):
        # In the export version we do not call serve(), but instead use export logic.
        serve()


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
    audio_book_app = AudioBookApp(audio_book)
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
