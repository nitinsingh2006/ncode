"""
Nitin Editor - preview.py
HTML/CSS preview panel using QWebEngineView.
"""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class PreviewPanel(QWidget):
    """Renders HTML/CSS code in an embedded web view."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet("background:#1a1a2e; border-bottom: 1px solid #313244;")
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(8, 0, 8, 0)
        title = QLabel("🌐  HTML / CSS Preview")
        title.setStyleSheet("color:#cdd6f4; font-size:12px; font-weight:bold;")
        hbox.addWidget(title)
        hbox.addStretch()
        self._layout.addWidget(header)

        if HAS_WEBENGINE:
            self._view = QWebEngineView()
            self._view.setStyleSheet("background:#ffffff;")
            self._layout.addWidget(self._view)
        else:
            msg = QLabel(
                "⚠  QtWebEngine not available.\n\n"
                "Install with:\n"
                "   pip install PySide6-WebEngine\n\n"
                "HTML preview requires QtWebEngine."
            )
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet(
                "color:#f38ba8; font-size:13px; background:#1e1e2e;"
            )
            self._layout.addWidget(msg)

    def render_html(self, html: str) -> None:
        """Render raw HTML content in the preview."""
        if HAS_WEBENGINE:
            self._view.setHtml(html, QUrl("about:blank"))

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
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
{css}
</style>
</head>
<body>
  <h1>CSS Preview</h1>
  <h2>Heading 2</h2>
  <p>This is a paragraph with some <strong>bold</strong> and <em>italic</em> text.</p>
  <a href="#">A sample link</a>
  <ul>
    <li>List item 1</li>
    <li>List item 2</li>
    <li>List item 3</li>
  </ul>
  <button>Sample Button</button>
  <div class="container">
    <p class="text">Styled container</p>
  </div>
</body>
</html>"""
        self.render_html(html)
