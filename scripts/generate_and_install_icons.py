"""
Nitin Editor — Icon Generator and System Installer
Generates SVG and PNG icon assets across all standard resolutions
and installs them into user-local icon themes (~/.local/share/icons/hicolor).
"""
import os
import shutil
import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

SVG_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#181825" />
      <stop offset="50%" stop-color="#1e1e2e" />
      <stop offset="100%" stop-color="#11111b" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#89b4fa" />
      <stop offset="100%" stop-color="#74c7ec" />
    </linearGradient>
    <linearGradient id="codeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#a6e3a1" />
      <stop offset="100%" stop-color="#89dceb" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Base Rounded Card -->
  <rect x="16" y="16" width="480" height="480" rx="96" fill="url(#bg)" stroke="#313244" stroke-width="4" />

  <!-- Window Header Bar -->
  <rect x="16" y="16" width="480" height="96" rx="96" fill="#181825" />
  <rect x="16" y="80" width="480" height="32" fill="#181825" />

  <!-- Window Dots -->
  <circle cx="72" cy="64" r="14" fill="#f38ba8" />
  <circle cx="116" cy="64" r="14" fill="#f9e2af" />
  <circle cx="160" cy="64" r="14" fill="#a6e3a1" />

  <!-- Divider Line -->
  <line x1="16" y1="112" x2="496" y2="112" stroke="#313244" stroke-width="3" />

  <!-- Main Code Bracket Symbol </> -->
  <g filter="url(#glow)">
    <!-- < -->
    <path d="M 170 210 L 90 280 L 170 350" fill="none" stroke="url(#accent)" stroke-width="36" stroke-linecap="round" stroke-linejoin="round" />
    <!-- / -->
    <line x1="280" y1="185" x2="232" y2="375" stroke="#f5e0dc" stroke-width="32" stroke-linecap="round" />
    <!-- > -->
    <path d="M 342 210 L 422 280 L 342 350" fill="none" stroke="url(#codeGrad)" stroke-width="36" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bottom Terminal Prompt Indicator -->
  <text x="72" y="440" font-family="monospace" font-size="38" font-weight="bold" fill="#89b4fa">ncode_</text>
</svg>
"""


def render_svg_to_png(svg_data: str, size: int) -> QImage:
    renderer = QSvgRenderer(svg_data.encode("utf-8"))
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))  # Transparent background
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    return img


def main():
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    root_dir = Path(__file__).parent.parent.resolve()
    assets_dir = root_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    svg_path = assets_dir / "icon.svg"
    png_path = assets_dir / "icon.png"

    print("▶ Writing master SVG icon...")
    svg_path.write_text(SVG_CONTENT, encoding="utf-8")

    print("▶ Rendering master 512x512 PNG icon...")
    img512 = render_svg_to_png(SVG_CONTENT, 512)
    img512.save(str(png_path), "PNG")

    # User icon theme base directory
    user_icons_dir = Path.home() / ".local" / "share" / "icons" / "hicolor"

    # Install scalable SVG
    scalable_dir = user_icons_dir / "scalable" / "apps"
    scalable_dir.mkdir(parents=True, exist_ok=True)
    (scalable_dir / "nitin-editor.svg").write_text(SVG_CONTENT, encoding="utf-8")

    # Install resolutions
    resolutions = [16, 24, 32, 48, 64, 128, 256, 512]
    for r in resolutions:
        res_dir = user_icons_dir / f"{r}x{r}" / "apps"
        res_dir.mkdir(parents=True, exist_ok=True)
        img = render_svg_to_png(SVG_CONTENT, r)
        target_png = res_dir / "nitin-editor.png"
        img.save(str(target_png), "PNG")

    print("✓ Icon assets generated and installed into ~/.local/share/icons/hicolor/")

    # Update GTK icon cache if binary available
    if shutil.which("gtk-update-icon-cache"):
        try:
            subprocess.run(
                ["gtk-update-icon-cache", "-f", "-t", str(user_icons_dir)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("✓ GTK icon cache updated")
        except Exception:
            pass


if __name__ == "__main__":
    main()
