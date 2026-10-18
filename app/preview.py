"""
Nitin Editor - preview.py
HTML/CSS preview panel using QWebEngineView with safe QTextBrowser fallback
and direct Default Browser launcher.
"""
from __future__ import annotations

import tempfile
import webbrowser
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextBrowser
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except Exception:  # In case of missing lib or Wayland init failure
    HAS_WEBENGINE = False


def open_in_default_browser(html_or_css: str, is_css: bool = False) -> str:
    """Write HTML/CSS to a temporary file and open in the default browser."""
    if is_css:
        content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>CSS Preview</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; background: #fafafa; color: #1e1e2e; }}
{html_or_css}
</style>
</head>
<body>
  <h1>CSS Preview</h1>
  <h2>Sample Heading</h2>
  <p>This is a paragraph demonstrating styled text with <strong>bold</strong> and <em>italic</em>.</p>
  <button style="padding: 8px 16px; cursor: pointer;">Sample Button</button>
  <div class="container" style="margin-top: 16px; padding: 16px; border: 1px solid #ccc; border-radius: 8px;">
    <p>Container box content</p>
  </div>
</body>
</html>"""
    else:
        content = html_or_css

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(content)
        temp_path = f.name

    webbrowser.open(f"file://{Path(temp_path).resolve()}")
    return temp_path


class PreviewPanel(QWidget):
    """Renders HTML/CSS code with embedded view and open in default browser support."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_html: str = ""
        self._is_css: bool = False
        self._webengine_view = None
        self._text_browser: Optional[QTextBrowser] = None

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet("background:#1a1a2e; border-bottom: 1px solid #313244;")
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(10, 0, 10, 0)
        hbox.setSpacing(10)

        title = QLabel("🌐  HTML / CSS Live Preview")
        title.setStyleSheet("color:#cdd6f4; font-size:12px; font-weight:bold;")
        hbox.addWidget(title)

        hbox.addStretch()

        browser_btn = QPushButton("🌍  Open in Default Browser")
        browser_btn.setToolTip("Open this page directly in your system default browser (Chrome, Firefox, etc.)")
        browser_btn.setStyleSheet(
            "QPushButton { background: #313244; color: #89b4fa; border: 1px solid #45475a; "
            "border-radius: 4px; padding: 3px 12px; font-size: 11px; font-weight: bold; } "
            "QPushButton:hover { background: #45475a; color: #b4befe; border-color: #89b4fa; }"
        )
        browser_btn.clicked.connect(self._on_browser_clicked)
        hbox.addWidget(browser_btn)

        self._layout.addWidget(header)

        # Try to initialize WebEngine view safely
        if HAS_WEBENGINE:
            try:
                self._webengine_view = QWebEngineView(self)
                self._webengine_view.setStyleSheet("background:#ffffff;")
                self._layout.addWidget(self._webengine_view)
            except Exception:
                self._webengine_view = None

        if self._webengine_view is None:
            # Crash-proof fallback using native Qt QTextBrowser
            self._text_browser = QTextBrowser(self)
            self._text_browser.setOpenExternalLinks(True)
            self._text_browser.setStyleSheet(
                "background:#ffffff; color:#11111b; padding:12px; font-size:13px; border:none;"
            )
            self._layout.addWidget(self._text_browser)

    def _on_browser_clicked(self) -> None:
        if self._current_html:
            open_in_default_browser(self._current_html, self._is_css)

    def render_html(self, html: str) -> None:
        """Render raw HTML content in the preview."""
        self._current_html = html
        self._is_css = False
        if self._webengine_view is not None:
            try:
                self._webengine_view.setHtml(html, QUrl("about:blank"))
                return
            except Exception:
                pass
        if self._text_browser is not None:
            self._text_browser.setHtml(html)

    def render_html_with_css(self, html: str, css: str) -> None:
        """Wrap CSS inside the HTML and render."""
        combined = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{css}
</style>
</head>
<body>
{html}
</body>
</html>"""
        self.render_html(combined)

    def render_css_only(self, css: str) -> None:
        """Show CSS preview with a sample HTML document."""
        self._is_css = True
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; background: #fafafa; color: #1e1e2e; }}
{css}
</style>
</head>
<body>
  <h1>CSS Preview</h1>
  <h2>Sample Heading 2</h2>
  <p>This is a paragraph demonstrating styled text with <strong>bold</strong> and <em>italic</em>.</p>
  <a href="#">Sample link</a>
  <ul>
    <li>Item one</li>
    <li>Item two</li>
    <li>Item three</li>
  </ul>
  <button style="padding: 8px 16px; cursor: pointer;">Sample Button</button>
  <div class="container" style="margin-top: 16px; padding: 16px; border: 1px solid #ccc; border-radius: 8px;">
    <p class="text">Styled container box</p>
  </div>
</body>
</html>"""
        self.render_html(html)
