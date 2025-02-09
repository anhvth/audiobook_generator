import re
from starlette.responses import FileResponse, RedirectResponse
from starlette.exceptions import HTTPException
from loguru import logger

# Adjusted imports to bring in UI components explicitly
# from fasthtml.common import fast_app, serve, NotStr, ft_hx, MarkdownJS, Style, Script
from fasthtml.common import *
# from fasthtml import *
# .ui import Titled, Div, A, Li, Ul, H2, H3, Button
def extract_headings_and_assign_ids(md_text: str):
    """
    1) Looks for lines that start with '#' or '##'.
    2) Replaces them with <h1> or <h2> (with an auto-generated id).
    3) Returns:
       - transformed_md: the updated markdown string (still suitable for MarkdownJS to parse),
       - headings: a list of (heading_text, heading_id, level).
    """
    lines = md_text.splitlines()
    headings = []
    new_lines = []
    for line in lines:
        # Match lines that begin with # or ##
        match = re.match(r'^(#{1,2})\s+(.*)$', line)
        if match:
            level = len(match.group(1))  # 1 or 2
            heading_text = match.group(2).strip()
            # Build an ID (lowercase and replace non-alphanumerics with '-')
            heading_id = re.sub(r'[^a-zA-Z0-9]+', '-', heading_text.lower()).strip('-')
            # Save info for building a nav menu
            headings.append((heading_text, heading_id, level))
            # Replace the line with actual HTML <h1>/<h2> so we can anchor to it
            line = f'<h{level} id="{heading_id}">{heading_text}</h{level}>'
        new_lines.append(line)
    transformed_md = "\n".join(new_lines)
    return transformed_md, headings


class AudioBookApp:
    def __init__(self, audio_book, book_name):
        self.audio_book = audio_book
        self.book_name = book_name

        # First, parse headings and store them
        for item in self.audio_book.items:
            new_md, headings = extract_headings_and_assign_ids(item["text_md"])
            item["text_md"] = new_md
            item["headings"] = headings

        # Second, assign each page a "page_title"
        # If a page has at least one heading, use the first heading’s text.
        # If it has no headings, inherit the previous page's title (or "Untitled" for page 0).
        for i, item in enumerate(self.audio_book.items):
            if item["headings"]:
                item["page_title"] = item["headings"][0][0]
            else:
                if i > 0:
                    item["page_title"] = self.audio_book.items[i - 1]["page_title"]
                else:
                    item["page_title"] = ""

        # Now build the FastHTML app with updated CSS styles
        self.app, self.rt = fast_app(
            pico=True,
            hdrs=(
                MarkdownJS(),  # So the in-page markdown is rendered in the browser
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
.header .logo {
    font-size: 1.8em;
    font-weight: bold;
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

/* Layout container: side menu + main content */
.layout {
    display: flex;
    gap: 1rem;
    margin: 2em auto;
    max-width: 1200px;
    padding: 0 1em;
}

/* Side menu styling */
.side-menu {
    flex: 0 0 250px;
    background: var(--container-bg);
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    padding: 1em;
    max-height: calc(100vh - 5em);
    overflow-y: auto;
}

/* Book info in side menu */
.book-info {
    text-align: center;
    margin-bottom: 1em;
}
.book-info h2 {
    font-size: 1.6em;
    margin: 0;
}

/* Nearby pages list styling */
.chapter-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.chapter-list li {
    margin: 0.5em 0;
    padding: 0.3em;
    border-radius: 4px;
}
.chapter-list li:hover {
    background: var(--link-secondary-bg);
}
.chapter-list li.active {
    font-weight: bold;
    background: #5c6d70;  /* changed */
    color: #fff5e1;       /* changed */
}

/* Headings for sections in side menu */
.side-menu h3 {
    font-size: 1.2em;
    margin: 1em 0 0.5em;
}

/* Main content container with page-turn animation */
.main-content {
    flex: 1;
    background: var(--container-bg);
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    animation: pageTurn 0.8s ease;
    transform-style: preserve-3d;
    padding: 1.5em;
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

/* Next/Prev Navigation Buttons */
.nav {
    display: flex;
    justify-content: space-between;
    margin-top: 2em;
}
.nav a {
    font-size: 1.1em;
    text-decoration: none;
    padding: 0.5em 1em;
    border-radius: 4px;
    transition: background 0.3s;
}
.nav a.secondary {
    background: var(--link-secondary-bg);
    color: var(--link-secondary-text);
}
.nav a.primary {
    background: var(--link-primary-bg);
    color: var(--link-primary-text);
}
.nav a:hover {
    opacity: 0.8;
}

/* ----- Theme Toggle Script ----- */
                    """
                ),
                Script(
                    """
function setTheme(theme) {
    if (theme === 'auto') {
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
         if (btn.textContent.toLowerCase() === theme) {
              btn.classList.add('active');
         } else {
              btn.classList.remove('active');
         }
    });
}

// Add keyboard navigation and volume control
document.addEventListener('keydown', function(e) {
    const audio = document.querySelector('audio');
    
    switch(e.key) {
        case 'ArrowRight':
        case ' ':  // spacebar
            const nextBtn = document.querySelector('.nav a.primary');
            if (nextBtn) nextBtn.click();
            break;
            
        case 'ArrowLeft':
            const prevBtn = document.querySelector('.nav a.secondary');
            if (prevBtn) prevBtn.click();
            break;
            
        case 'ArrowUp':
            if (audio) {
                audio.volume = Math.min(1, audio.volume + 0.1);
                e.preventDefault();
            }
            break;
            
        case 'ArrowDown':
            if (audio) {
                audio.volume = Math.max(0, audio.volume - 0.1);
                e.preventDefault();
            }
            break;
    }
});

window.addEventListener('load', function(){
    var storedTheme = localStorage.getItem('theme') || 'auto';
    setTheme(storedTheme);
    
    // Add page turn animation class when navigating
    document.querySelectorAll('.nav a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            document.querySelector('.main-content').style.animation = 'pageTurn 0.8s ease';
            setTimeout(() => {
                window.location.href = href;
            }, 400);
        });
    });
});
                    """
                ),
            ),
            static_path="./assets",
            debug=True,
        )
        self.setup_routes()

    def setup_routes(self):
        @self.rt("/")
        def home():
            return RedirectResponse("/0")

        @self.rt("/assets/{fname:path}")
        def static_assets(fname: str):
            path = self.audio_book.assets_dir / fname
            if path.exists():
                logger.info(f"Serving file: {path}")
                return FileResponse(path)
            logger.error(f"File not found: {path}")
            raise HTTPException(status_code=404, detail="File not found")

        @self.rt("/{idx:int}")
        def page(idx: int):
            if not 0 <= idx < len(self.audio_book.items):
                logger.error(f"Invalid page index: {idx}")
                raise HTTPException(status_code=404, detail="Page not found")

            item = self.audio_book.items[idx]

            # -----------------------------------------------
            # 1) Build the side menu
            # -----------------------------------------------
            book_info = Div(
                H2(self.book_name, style="margin:0;"),
                ft_hx("hr"),
                cls="book-info"
            )

            # Build a list of nearby pages (5 before and 5 after)
            start_idx = max(0, idx - 5)
            end_idx = min(len(self.audio_book.items), idx + 6)
            chapter_list_items = []
            for p in range(start_idx, end_idx):
                display_text = f"{self.audio_book.items[p]['page_title']} (Page {p+1})"
                li = Li(A(display_text, href=f"/{p}"))
                if p == idx:
                    li.attrs["class"] = "active"
                chapter_list_items.append(li)
            chapter_list = Ul(*chapter_list_items, cls="chapter-list")

            nearby_section = Div(
                H3("Nearby Pages"),
                chapter_list
            )

            # Build the table of contents from in-page headings
            headings = item.get("headings", [])
            if headings:
                toc_links = []
                for text, hid, level in headings:
                    indent = "margin-left:1em;" if level == 2 else ""
                    toc_links.append(A(text, href=f"#{hid}", style=indent))
                toc_section = Div(
                    H3("Contents"),
                    Div(*toc_links)
                )
            else:
                toc_section = Div(
                    H3("Contents"),
                    Div("No headings found.")
                )

            side_menu = Div(
                book_info,
                nearby_section,
                ft_hx("hr"),
                toc_section,
                cls="side-menu"
            )

            # -----------------------------------------------
            # 2) Build the main content area
            # -----------------------------------------------
            image_content = Div()
            if "image" in item:
                image_content = ft_hx(
                    "img",
                    src=f"/assets/{item['image']}",
                    alt="Generated Image",
                    style="max-width:100%; margin-bottom:1em;"
                )

            text_markdown = Div(NotStr(item["text_md"]), cls="markdown marked")
            audio_player = ft_hx("audio", controls=True, autoplay=True, src=f"/assets/{item['audio']}")
            nav_links = self._create_navigation(idx)
            navigation = Div(*nav_links, cls="nav")

            main_content = Div(
                image_content,
                text_markdown,
                audio_player,
                navigation,
                cls="main-content"
            )

            layout_div = Div(side_menu, main_content, cls="layout")

            header_div = Div(
                Div('AudiobookNhaLam', cls="logo"),
                # Div(
                #     Button("Light", onclick="setTheme('light');"),
                #     Button("Dark", onclick="setTheme('dark');"),
                #     Button("Auto", onclick="setTheme('auto');"),
                #     cls="theme-toggle"
                # ),
                cls="header"
            )

            return Titled(
                f"Page {idx+1} of {len(self.audio_book.items)}",
                header_div,
                layout_div
            )

    def _create_navigation(self, idx):
        nav = []
        if idx > 0:
            nav.append(A("⟵ Previous", href=f"/{idx-1}", cls="secondary"))
        if idx < len(self.audio_book.items) - 1:
            nav.append(A("Next ⟶", href=f"/{idx+1}", cls="primary"))
        return nav

    def run(self):
        serve()
