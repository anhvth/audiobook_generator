# --- Import FastHTML and Starlette classes
from fasthtml.common import *
from starlette.responses import FileResponse, RedirectResponse
from starlette.exceptions import HTTPException
from loguru import logger

# --- For text processing and TTS

# --- For image generation


class AudioBookApp:
    def __init__(self, audio_book, book_name):
        self.audio_book = audio_book
        self.book_name = book_name
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
                H1(self.book_name),
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
